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
    get_full_path,
    Request
)


class Downloader:
    def __init__(self):
        self.url = None
        self.file = None
        self.path = None
        self.path_with_file = None
        self.stream = True

    def download(self, data: tuple, path: pathlib.Path) -> None:
        """
        The main download action

        :return:    Nothing
        """
        self.file, self.url = data
        self.path = path
        self.path_with_file = self.path.joinpath(self.file)

        if not is_valid_path(self.path_with_file, strict=True):
            print(f"The file: {self.file} already exists, skipping")
        else:
            print(f"Downloading {self.file}")

            # DEBUG
            self.url = "https://i.ytimg.com/vi/0KEv38tAWm4/maxresdefault.jpg"

            response = Request(self.url, stream=self.stream).response

            if response is None or response.status_code != requests.codes.ok:
                print(f"Failed to download: {self.file} ")
            elif response.status_code == requests.codes.ok:
                self.write_to_disk(response.raw)
                if self.stream:
                    response.close()

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


class Mod:
    def __init__(self, minecraft: str, project_id: str, file_id: str):
        """
        Creates a Mod object which holds the url
         to download the mod file from

        :param project_id:   The projectID
        :param file_id:      The fileID
        """
        self.minecraft = minecraft
        self.project_id = project_id
        self.file_id = file_id
        self.api = f"https://api.cfwidget.com/minecraft/mc-mods/{self.project_id}"
        self.file = None
        self.url = self.generate_url_via_api()

    def generate_url_via_api(self):
        """
        Construct an url which directly points to media.forgecdn.net
         with info gathererd from the CurseForge Widget API
        Because curseforge.com redirects to edge.forgecdn.net, which redirects to media.forgecdn.net
         and somewhere along the way CloudFlare is nagging about a captcha, resulting in a 403
        So this seems to be the only working solution to avoid the CloudFlare captcha, but
         I have no idea how reliable it is

        :return:    The actual file download url, or None when mod is not available
        """

        while True:
            data = Request(self.api).response
            data_json = json.loads(data.content)
            # When a mod has not been accessed before via the API it returns an error response, but
            #  the mod is queued for fetch and it says to retry the request after 10 seconds
            if "error" in data_json:
                print(f"Project {self.project_id} is queued for fetch, waiting 2 seconds")
                time.sleep(2)
            else:
                break

        # The "download" key holds the main download, which I think is the most recent stable verison
        #  and all the other versions are stored in "versions" split up by minecraft version
        data_point = data_json["download"]
        if data_point["id"] != self.file_id:
            # Hopefully this is safe to do
            # TODO: Make sure to test if it actually is
            data_point = data_json["versions"][self.minecraft]
            for mod in data_point:
                if mod["id"] == self.file_id:
                    data_point = mod
                    break

        if isinstance(data_point, dict):
            self.file = data_point["name"]
            data_point["id"] = str(data_point["id"])

            # I don't understand the logic behind these forgecdn urls, but it seems they just split
            #  the fileID after the 4th number
            # TODO: Make sure to test this thoroughly too
            url = f"https://media.forgecdn.net/files/{data_point['id'][:4]}/{data_point['id'][4:]}/{self.file}"
            return url
        else:
            print(f"Error: {self.project_id} does not contain a file with id: {self.file}")
            return None


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

    modpack_info["name"] = f"{manifest_json['name']} v{manifest_json['version']}"
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
    modpack_info: dict = parse_manifest(args["manifest"])
    downloader = Downloader()

    print(f"Starting download of: {modpack_info['name']}")
    pprint(args)
    pprint(modpack_info)

    if args["include_forge"]:
        forge = Forge(modpack_info["minecraft"], modpack_info["forge"])
        downloader.download((forge.file, forge.url), args["directory"])

    for m in modpack_info["mods"]:
        mod = Mod(modpack_info["minecraft"], m["projectID"], m["fileID"])
        if mod.url is not None:
            downloader.download((mod.file, mod.url), args["mods_folder"])


if __name__ == "__main__":
    main()
