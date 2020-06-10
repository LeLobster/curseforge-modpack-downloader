#!/usr/bin/env python3

import os
import pathlib


def get_path_as_path_obj(path) -> pathlib.Path:
    """
    Converts a string version of path to
     a Path object if needed

    :param path:    The path to check
    :return:        The Path object
    """
    if isinstance(path, str):
        return pathlib.Path(path)
    return path


def get_full_path(path) -> pathlib.Path:
    """
    Expands a relative path to absolute, and
     resolves symlinks if needed

    :param path:    The path to check
    :return:        An absolute path
    """
    path = get_path_as_path_obj(path)
    if not path.is_absolute() or path.is_symlink():
        path = path.resolve()
    return path


def is_valid_path(path, strict=False) -> bool:
    """
    Checks if a path is valid, ie
     if a file or directory exists, and
     if it is readable/writable

    :param path:    The path
    :param strict:  Don't allow path to already exist
    :return:        If the path is valid
    """
    path = get_path_as_path_obj(path)
    if path.exists() and not strict:
        if path.is_file():
            return os.access(str(path), os.R_OK)  # read
        elif path.is_dir():
            return os.access(str(path), os.W_OK)  # write
    elif not path.exists() and strict:
        return True
    else:
        return False
