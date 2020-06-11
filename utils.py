#!/usr/bin/env python3

import os
import pathlib

import requests


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
    try:
        if strict and path.exists():
            raise FileExistsError
        elif not strict and not path.exists():
            raise FileNotFoundError
        else:
            if path.is_file():
                return os.access(str(path), os.R_OK)  # read
            elif path.is_dir():
                return os.access(str(path), os.W_OK)  # write
            return True
    except (FileExistsError, FileNotFoundError):
        return False


def handle_get_request(url, headers, timeout, stream=False) -> requests.Response:
    """
    Make the get request, and
     attempt to handle errors somewhat nicely

    :return:    The request response
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout,
                                verify=True, stream=stream)
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
