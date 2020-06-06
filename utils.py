#!/usr/bin/env python3

import os
import pathlib


def get_full_path(path: str) -> pathlib.Path:
    """
    Expands a relative path to absolute, and
     resolves symlinks if needed

    :param path:    The path to check
    :return:        An absolute path
    """
    path = pathlib.Path(path)
    if not path.is_absolute() or path.is_symlink():
        path = path.resolve()
    return path


def is_valid_path(path: str) -> bool:
    """
    Checks if a path is valid, ie
     if a file or directory exists, and
     if it is readable/writable

    :param path:    The path
    :return:        If the path is valid
    """
    path = pathlib.Path(path)
    if path.exists():
        if path.is_file():
            return os.access(path, os.R_OK) and os.access(path, os.W_OK)
        return path.is_dir()
    return False
