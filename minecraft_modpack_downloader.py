#!/usr/bin/env python3

import argparse
import json
import pathlib
import shutil
import sys
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
            print(f"Downloading {self.file} to: {self.path}")

            response = Request(self.url, stream=True).response

            if response is not None:
                if response.status_code == requests.codes.ok:
                    self.write_to_disk(response.raw)

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
    def __init__(self, projectID: str, fileID: str):
        """
        Creates a Mod object which holds the url
         to download the mod file from

        :param projectID:   The projectID
        :param fileID:      The fileID
        """
        self.project = projectID
        self.file = fileID
        self.url_pre = f"https://www.curseforge.com/projects/{self.project}"

    def get_actual_url(self):
        """
        Constructs a new url, to actually download the mod from,
         with information retrieved from a request to a generic curseforge url
         because we can not directly construct the file url ourself

        :return:    The actual file url
        """
        pass

    def display_info(self):
        print(self.url_pre)


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

    pprint(args)
    pprint(modpack_info)

    if args["include_forge"]:
        forge = Forge(modpack_info["minecraft"], modpack_info["forge"])
        downloader.download((forge.file, forge.url), args["directory"])
    for m in modpack_info["mods"]:
        mod = Mod(m["projectID"], m["fileID"])
        mod.display_info()


if __name__ == "__main__":
    main()
