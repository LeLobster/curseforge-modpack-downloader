#!/usr/bin/env python3

import os
import pathlib


def get_full_path(path: str, to_string=False):
    """
    Expands a relative path to absolute, and
     resolves symlinks if needed

    :param path:        string  - The path to check
    :param to_string:   boolean - Convert to str before returning?
    :return:            Path    - An absolute path
    """
    path = pathlib.Path(path)
    if not path.is_absolute() or path.is_symlink():
        path = path.resolve()
    return str(path) if to_string else path


def is_valid_path(path: str):
    """
    Checks if a path is valid, ie
     if a file or directory exists, and
     if it is readable/writable

    :param path:    string  - The path
    :return:        boolean - If the path is valid
    """
    path = pathlib.Path(path)
    if path.exists():
        if path.is_file():
            return os.access(path, os.R_OK) and os.access(path, os.W_OK)
        return True
    return False
