#!/usr/bin/env python3

import os
import pathlib
import random
import time
from threading import Lock

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


class Request:
    def __init__(self, url, stream=False):
        self.status = 0
        self.attempt = 1
        self.timeout = 10
        self.retry_status = [500, 503, 504]
        self.retry_max = 3
        self.retry_sleep = 2.5
        self.headers = {"User-Agent": f"{get_random_useragent()}"}
        self.url = url
        self.stream = stream
        self.response = self.handle_get_request()

    def make_get_request(self) -> requests.Response:
        """
        Make the get request, and
         attempt to handle errors somewhat nicely

        :return:        The response
        """
        try:
            response = requests.get(
                self.url, headers=self.headers, timeout=self.timeout, verify=True, stream=self.stream
            )
            response.raise_for_status()

        except requests.exceptions.Timeout as e:
            # will also catch both ConnectTimeout and ReadTimeout
            safe_print("Timeout: The request timed out while waiting for the server to respond"
                       f"\n{e}")
            response = None
        # a 4XX client error or 5XX server error, potentially raised by raise_for_status
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            # noinspection PyUnboundLocalVariable
            if response.status_code == 403:
                safe_print("Forbidden: The request was not allowed")
            else:
                safe_print("Error: The requested resource could not be reached")
            print(e)
        # badly configured server?
        except requests.exceptions.TooManyRedirects as e:
            safe_print(f"Error: The request exceeded the number of maximum redirections\n{e}")
        except requests.exceptions.SSLError as e:
            safe_print(f"Error: The SSL certificate could not be verified\n{e}")
        except requests.exceptions.RequestException as e:
            safe_print(f"Encountered an ambiguous error, you're on your own now\n{e}")

        finally:
            if response is not None and not self.stream:
                # noinspection PyUnboundLocalVariable
                response.close()

        return response

    def handle_get_request(self) -> requests.Response:
        """
        Handle the get request's response

        :return:    The request response
        """

        while self.status != requests.codes.ok:
            response = self.make_get_request()
            self.status = response.status_code if response is not None else None

            if self.status not in self.retry_status:
                break

            self.attempt += 1
            if self.attempt > self.retry_max:
                # safe_print("All download attempts have failed, aborting")
                break
            else:
                pass
                # safe_print(f"Retrying...")
            time.sleep(self.retry_sleep)

        # noinspection PyUnboundLocalVariable
        return response


def get_random_useragent() -> str:
    """
    Retrieves a random user-agent string from a list

    :return:    The user-agent
    """
    user_agent = random.choice([
        "Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; OpenBSD amd64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux armv7l; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; FreeBSD i386; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; Linux aarch64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Intel Mac OS X 10_15_4; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Windows NT 6.2; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0"
    ])
    return user_agent


def safe_print(*a, **b):
    """
    A thread safe print function
    Temporarily locks a thread before printing

    :param a:   *values to print
    :param b:   **arguments
    :return:    Nothing
    """
    print_lock = Lock()
    with print_lock:
        print(*a, **b)
