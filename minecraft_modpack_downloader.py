#!/usr/bin/env python3

import argparse
import json
import pathlib
import shutil
import sys
import time
from pprint import pprint

import requests

from utils import (
    is_valid_path,
    get_full_path
)


class Downloader:
    def __init__(self):
        self.url = None
        self.file = None
        self.path = None
        self.path_with_file = None
        # TODO: Maybe implement user-agent randomizer
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0"}
        self.retry_status = [500, 503, 504]
        self.retry_max = 3
        self.retry_sleep = 2.5
        self.timeout = 10

    def download(self, data: tuple, path: pathlib.Path) -> None:
        """
        The main download action

        :return:    Nothing
        """
        self.url, self.file = data
        self.path = path
        self.path_with_file = self.path.joinpath(self.file)

        if not is_valid_path(self.path_with_file, strict=True):
            print(f"The file: {self.file} already exists, skipping")
        else:
            status = 0
            attempt = 1

            print(f"Downloading {self.file} to: {self.path}")

            # DEBUG
            self.url = "https://i.ytimg.com/vi/0KEv38tAWm4/maxresdefault.jpg"
            print(self.url)

            while status != requests.codes.ok:
                response = self.handle_request()
                status = response.status_code

                if status not in self.retry_status:
                    break

                attempt += 1
                if attempt > self.retry_max:
                    print("All download attempts have failed, aborting")
                    break
                else:
                    print(f"Retrying...")
                time.sleep(self.retry_sleep)

            if status == requests.codes.ok:
                # noinspection PyUnboundLocalVariable
                self.write_to_disk(response.raw)

            response.close()

    def handle_request(self) -> requests.Response:
        """
        Make the get request, and
         attempt to handle errors somewhat nicely

        :return:    The request response
        """
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout,
                                    verify=True, stream=True)
            response.raise_for_status()

        # https://requests.readthedocs.io/en/master/api/#exceptions
        except requests.exceptions.Timeout as e:
            # will also catch both ConnectTimeout and ReadTimeout
            print(f"Timeout: The request timed out while waiting for the server to respond"
                  f"\n{e}")
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            # a 4XX client error or 5XX server error, potentially raised by raise_for_status
            print(
                "Error: The requested resource could not be reached. "
                "Please, make sure the url is correct and/or the destination is still reachable"
                f"\n{e}")
        except requests.exceptions.TooManyRedirects as e:
            # badly configured server?
            print(f"Error: The request exceeded the number of maximum redirections\n{e}")
        except requests.exceptions.SSLError as e:
            print(f"Error: The SSL certificate could not be verified\n{e}")
        except requests.exceptions.RequestException as e:
            print(f"Encountered an ambiguous error, you're on your own now\n{e}")

        # noinspection PyUnboundLocalVariable
        return response

    def write_to_disk(self, raw_data) -> None:
        """
        Write the raw data to disk

        :param raw_data:    The raw data
        :return:            Nothing
        """
        try:
            with self.path_with_file.open(mode="wb") as file:
                shutil.copyfileobj(raw_data, file)
        except Exception as e:
            print(f"Something went wrong while writing {self.file} to disk: {e}")
        else:
            print(f"{self.file} succesfully downloaded")


class Forge:
    def __init__(self, minecraft: str, forge: str):
        """
        Creates a Forge object which holds the url
         to download the Forge installer from

        :param minecraft:   Required minecraft version
        :param forge:       Required Forge version
        """
        self.version = f"{minecraft}-{forge}"
        self.file = f"forge-{self.version}-installer.jar"
        self.url_base = "https://files.minecraftforge.net/maven/net/minecraftforge/forge"
        self.url = self.generate_url()

    def generate_url(self) -> str:
        """
        The url generator

        :return:    The url
        """
        url = f"{self.url_base}/{self.version}/{self.file}"
        return url


def parse_manifest(manifest: pathlib.Path) -> dict:
    """
    Open the manifest file and extract mod info (projectID & fileID), and
     the required Forge version info

    :param manifest:    The manifest file
    :return:            The mods & forge info
    """
    modpack_info = {}

    with manifest.open(mode="r") as m:
        manifest_file = m.read()
        try:
            manifest_json = json.loads(manifest_file)
        except json.decoder.JSONDecodeError as e:
            m.close()
            sys.exit(f"An error occurred while parsing the manifest file\n\"{e}\"")
    print("Manifest file parsed succesfully")

    modpack_info["forge"] = manifest_json["minecraft"]["modLoaders"][0]["id"].replace("forge-", "")
    modpack_info["minecraft"] = manifest_json["minecraft"]["version"]
    modpack_info["mods"] = [mod for mod in manifest_json['files']]
    return modpack_info


def validate_args(arguments: dict) -> dict:
    """
    Check if the manifest file exists, and
     if a target directory is specified check if it is valid, or
     if no target directory is specified, use the parent dir
     of the manifest file

    :param arguments:   The arguments
    :return:            The updated and checked arguments
    """
    manifest_file = get_full_path(arguments["manifest"])

    if not is_valid_path(manifest_file):
        sys.exit(
            "The path specified for the manifest file is invalid\n"
            "Please verify that it exists and/or that you have the right permissions"
        )
    print("The path specified for the manifest file is valid")

    if arguments["directory"] is not None:
        target_dir = get_full_path(arguments["directory"])
    else:
        print("Download directory not specified, using manifest parent directory")
        target_dir = manifest_file.parent

    arguments["manifest"] = manifest_file
    arguments["directory"] = target_dir
    arguments["mods_folder"] = target_dir.joinpath("mods")

    if is_valid_path(arguments["mods_folder"], strict=True):
        print("Creating folder to store mods in")
        arguments["mods_folder"].mkdir(parents=True)

    return arguments


def init_argparse() -> argparse.ArgumentParser:
    """
    Initialize an argparser with arguments

    :return:    The argparser
    """
    parser = argparse.ArgumentParser()
    # TODO: Make help text more informative
    parser.add_argument("--manifest", "-m",
                        action="store", type=str, required=True,
                        help="modpack manifest file location")
    parser.add_argument("--directory", "-d",
                        action="store", type=str, required=False, default=None,
                        help="target download location")
    parser.add_argument("--include-forge", "-f",
                        action="store_true", required=False, default=False,
                        help="also download required forge installer")
    return parser


def main():
    args: dict = validate_args(
        vars(init_argparse().parse_args())
    )
    pprint(args)
    modpack_info: dict = parse_manifest(args["manifest"])
    pprint(modpack_info)
    downloader = Downloader()
    if args["include_forge"]:
        forge = Forge(modpack_info["minecraft"], modpack_info["forge"])
        downloader.download((forge.url, forge.file), args["directory"])


if __name__ == "__main__":
    main()
