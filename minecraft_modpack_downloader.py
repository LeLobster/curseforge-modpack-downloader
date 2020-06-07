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


class Forge:
    # TODO: Move the download/requests bit to separate class, which
    #  the Forge and Mod classes can inherit
    def __init__(self, path: pathlib.Path, minecraft: str, forge: str):
        """
        Generate the url to download Forge from, and
         attempt to download it using the requests module

        :param path:        Path to download Forge to
        :param minecraft:   Required minecraft version
        :param forge:       Required Forge version
        """
        self.version = f"{minecraft}-{forge}"
        self.jar = f"forge-{self.version}-installer.jar"
        self.url_base = "https://files.minecraftforge.net/maven/net/minecraftforge/forge"
        self.url_full = self.generate_url()
        self.path = path
        self.path_full = str(path.joinpath(self.jar))

    def generate_url(self) -> str:
        """
        The url generator

        :return:    The url
        """
        url = f"{self.url_base}/{self.version}/{self.jar}"
        return url

    def download(self) -> None:
        """
        The main download action

        :return:    Nothing
        """
        # self.url_full = "https://httpbin.org/delay/5"
        # self.url_full = "https://httpbin.org/status/404"
        # self.url_full = "https://httpbin.org/status/503"
        # self.url_full = "https://httpbin.org/get"
        self.url_full = "https://i.ytimg.com/vi/0KEv38tAWm4/maxresdefault.jpg"

        # TODO: Figure out how to handle already existing jar file
        if not is_valid_path(self.path_full, strict=True):
            print("The Forge installer already exists at the specified location, removing")
            pathlib.Path(self.path_full).unlink()

        response = ""
        status = 0
        attempt = 1
        retry = [500, 503, 504]

        print(f"Downlading {self.jar} to: {self.path}")
        print(self.url_full)
        while status != requests.codes.ok:
            response = self.handle_request()
            status = response.status_code

            if status not in retry:
                break

            attempt += 1
            if attempt > 3:
                print("All download attempts have failed, aborting")
                break
            else:
                print(f"Retrying...")
            time.sleep(2.5)

        if status == requests.codes.ok:
            self.write_to_disk(response.raw)
            print("Forge succesfully downloaded")

    def handle_request(self) -> requests.Response:
        """
        Make the get request, and
         attempt to handle errors somewhat nicely

        :return:    The request response
        """
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0"}

        try:
            response = requests.get(self.url_full, headers=headers, stream=True, timeout=10)
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
        except requests.exceptions.RequestException as e:
            print(f"Encountered an ambiguous error, you're on your own now\n{e}")

        finally:
            # noinspection PyUnboundLocalVariable
            return response

    def write_to_disk(self, raw_data) -> None:
        """
        Write the raw data to disk

        :param raw_data:    The raw data
        :return:            Nothing
        """
        try:
            with open(self.path_full, "wb") as file:
                shutil.copyfileobj(raw_data, file)
        except Exception as e:
            print(f"Something went wrong while writing file to disk: {e}")


def parse_manifest(manifest: pathlib.Path) -> dict:
    """
    Open the manifest file and extract mod info (projectID & fileID), and
     the required Forge version info

    :param manifest:    The manifest file
    :return:            The mods & forge info
    """
    modpack_info = {}

    with manifest.open() as m:
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

    if not is_valid_path(str(manifest_file)):
        sys.exit(
            "The path specified for the manifest file is invalid\n"
            "Please verify that it exists and/or that you have the right permissions"
        )
    else:
        print("The path specified for the manifest file is valid")

    if arguments["directory"] is not None:
        target_dir = get_full_path(arguments["directory"])
    else:
        print("Download directory not specified, using manifest parent directory")
        target_dir = manifest_file.parent

    arguments["manifest"] = manifest_file
    arguments["directory"] = target_dir
    arguments["mods_folder"] = target_dir.joinpath("mods")

    if not is_valid_path(str(arguments["mods_folder"])):
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
    if args["include_forge"]:
        Forge(args["directory"], modpack_info["minecraft"], modpack_info["forge"]).download()


if __name__ == "__main__":
    main()
