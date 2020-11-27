#!/bin/env python
"""
Put module documentation here
"""

import sys

import NOMADSExplorer.explore.discovery as discovery


class Nomad(object):
    def __init__(self, address: str = None, explorer: str = "remote"):
        if explorer not in discovery.EXPLORERS:
            message = "{} is not a valid explorer; only the following are supported: {}".format(
                explorer,
                ", ".join(discovery.EXPLORERS)
            )
            print(message, file=sys.stderr)
            exit(-1)

        if explorer == "local" and address is None:
            message = "An address must be supplied if looking for files locally"
            print(message, file=sys.stderr)
            exit(-1)

        self.address = address
        self.explorer = explorer
        self.directory = None
        self.loaded = False

    def explore(self):
        self.directory = discovery.discover(explorer=self.explorer, url=self.address)
        self.loaded = True

    def file_count(self) -> int:
        pass
