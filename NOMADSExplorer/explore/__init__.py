#!/bin/env python
"""
Put module documentation here
"""

from argparse import ArgumentParser


def create_commandline_parser() -> ArgumentParser:
    """
    Creates a command line parser for the script
    
    :rtype: ArgumentParser
    :return: An argument parser used to collect the inputs to the script
    """
    parser = ArgumentParser("This is the default description of a python script")
    # parser.add_argument(
    #    -o,
    #    metavar="example",
    #    dest="example",
    #    type=str,
    #    default="ex",
    #    help="This is an example argument used for an example"
    # )
    return parser


def main():
    """
    This is the entry point to the script's execution
    """
    parser = create_commandline_parser()
    parameters = parser.parse_args()


    # Run the following if this script was called directly


if __name__ == "__main__":
    main() 