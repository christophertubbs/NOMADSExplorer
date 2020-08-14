#!/bin/env python
"""
Put module documentation here
"""

import json

from argparse import ArgumentParser

import explore.web as web
import explore.local as local

EXPLORERS = {
    "local": local,
    "remote": web
}


def discover(explorer: str = "remote", url: str = None) -> dict:
    return EXPLORERS.get(explorer, web).get_directory(url)


def create_commandline_parser() -> ArgumentParser:
    """
    Creates a command line parser for the script
    
    :rtype: ArgumentParser
    :return: An argument parser used to collect the inputs to the script
    """
    parser = ArgumentParser("This is the default description of a python script")
    parser.add_argument(
        "-e",
        metavar="explorer",
        dest="explorer",
        choices=["local", "remote"],
        default="remote",
        help="What to explore"
    )
    parser.add_argument("-a", metavar="address", type=str, dest="address", help="Where to explore")
    parser.add_argument("target", type=str, default="nwm_directory.json", help="Where to put the discovered directory")
    return parser


def main():
    """
    This is the entry point to the script's execution
    """
    parser = create_commandline_parser()
    parameters = parser.parse_args()

    directory = discover(parameters.explorer, parameters.address)

    with open(parameters.target, "w") as json_file:
        json.dump(directory, json_file)

# Run the following if this script was called directly
if __name__ == "__main__":
    main() 