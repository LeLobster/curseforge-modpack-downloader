#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint

from utils import (
    is_valid_path,
    get_full_path
)


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
        print("The path specified for the manifest file is A-OK")

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


if __name__ == '__main__':
    main()
