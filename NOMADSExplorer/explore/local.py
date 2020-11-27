#!/bin/env python
"""
Put module documentation here
"""

import NOMADSExplorer.explore.directory as directory


def get_directory(url: str, verbose=False) -> directory.Directory:
    directory_contents = directory.Directory(url)

    return directory_contents
