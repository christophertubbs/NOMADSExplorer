#!/bin/env python
"""
Put module documentation here
"""

import NOMADSExplorer.explore.catalog as directory


def get_directory(url: str, verbose=False) -> directory.Catalog:
    directory_contents = directory.Catalog(url)

    return directory_contents
