#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from pprint import pprint

from utils import (
    is_valid_path,
    get_full_path
)


def parse_manifest(manifest: Path, forge: bool):
    """
    Open the manifest file and extract mod info (projectID & fileID), and
     the required Forge version info

    :param manifest:    Path    - The manifest file
    :param forge:       boolean - Include forge version?
    :return:            dict    - Containing mods & forge info
    """
    modpack_info = {}

    with manifest.open() as m:
        manifest_file = m.read()
        try:
            manifest_json = json.loads(manifest_file)
            print("Manifest file parsed succesfully")
        except json.decoder.JSONDecodeError as e:
            m.close()
            sys.exit(f"An error occurred while parsing the manifest file\n\"{e}\"")

    if forge:
        modpack_info["forge"] = manifest_json["minecraft"]["modLoaders"][0]["id"].replace("forge-", "")
    else:
        modpack_info["forge"] = None
    modpack_info["minecraft"] = manifest_json["minecraft"]["version"]

    modpack_info["mods"] = [mod for mod in manifest_json['files']]
    return modpack_info


def validate_args(arguments: dict):
    """
    Check if the manifest file exists, and
     if a target directory is specified check if it is valid, or
     if no target directory is specified, use the parent dir
     of the manifest file

    :param arguments:   dict - The arguments
    :return:            dict - The updated and checked arguments
                                with paths converted to Path objects
    """
    manifest_file = get_full_path(arguments["manifest"])

    if not is_valid_path(manifest_file):
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

    if not is_valid_path(arguments["mods_folder"]):
        print("Creating folder to store mods in")
        arguments["mods_folder"].mkdir(parents=True)

    return arguments


def init_argparse():
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
    args = validate_args(
        vars(init_argparse().parse_args())
    )
    pprint(args)
    modpack_info = parse_manifest(args["manifest"], args["include_forge"])
    pprint(modpack_info)


if __name__ == '__main__':
    main()
