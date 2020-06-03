#! /usr/bin/env python3

import argparse
from pprint import pprint


def init_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", "-m",
                        action="store", type=str, required=True,
                        help="mod manifest file location")
    parser.add_argument("--directory", "-d",
                        action="store", type=str, required=False, default=None,
                        help="target download location")
    parser.add_argument("--include-forge", "-f",
                        action="store_true", required=False, default=False,
                        help="also download required forge installer")
    return parser


def main():
    args = vars(init_argparse().parse_args())
    pprint(args)


if __name__ == '__main__':
    main()
