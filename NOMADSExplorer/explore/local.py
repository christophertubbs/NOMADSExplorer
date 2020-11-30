#!/bin/env python
"""
Put module documentation here
"""

import sys
import os
import typing
import logging

from datetime import datetime

import NOMADSExplorer.explore.catalog as catalog
import NOMADSExplorer.common as common

_DAY_FORMAT = "%Y%m%d"

LOADER_MODULE = sys.modules[__name__]


def form_configuration(day: catalog.Day, address: str, directory: str) -> catalog.Configuration:
    """
    Form a Configuration object based on a parsed link

    :param day: The day of which this configuration coincides
    :param address: The address for the directory that contained this configuration
    :param directory: The directory for the configuration
    :return: A configuration object that may contain individual forecasts
    """
    member = common.get_int_from_word(directory)

    if member is None:
        configuration = directory
    else:
        configuration = directory.replace("_mem" + str(member), "")

    return catalog.Configuration(
        configuration_type=configuration.strip("/"),
        address=os.path.join(address, directory),
        loader_module=LOADER_MODULE,
        day=day
    )


def form_configuration_file(directory: str, filename: str) -> catalog.File:
    """
    Creates metadata for files that belong to a configuration

    :param directory: The directory for the configuration
    :param filename: the name of the file in the configuration
    :return: An object containing the metadata for the discovered file
    """
    attributes = common.extract_file_attributes(filename)
    configuration_file = catalog.File(
        name=filename,
        address=os.path.join(directory, filename),
        reference=attributes['reference'],
        configuration=attributes['configuration'],
        model_type=attributes['model_type'],
        step=attributes['step'],
        area=attributes['area'],
        member=attributes.get("member")
    )
    return configuration_file


def get_catalog(url: str = None) -> catalog.Catalog:
    if url is None:
        url = ""

    catalog_contents = catalog.Catalog(url, loader_module=LOADER_MODULE)

    for directory in os.listdir(url):
        if directory.startswith("nwm"):
            date = datetime.strptime(directory[4:-1], _DAY_FORMAT)
            catalog_contents[date] = catalog.Day(
                date=date,
                name=directory.strip("/"),
                address=os.path.join(url, directory),
                loader_module=LOADER_MODULE
            )

    logging.debug("{} forecast days were found for a new catalog".format(len(catalog_contents)))

    return catalog_contents


def fetch_configurations(day: catalog.Day) -> typing.List[catalog.Configuration]:
    logging.debug("Getting configurations for {}".format(day))

    discovered_configurations = [
        form_configuration(
            day,
            day.address,
            directory
        )
        for directory in os.listdir(day.address)
        if os.path.isdir(os.path.join(day.address, directory))
    ]

    logging.debug("{} configurations found for {}".format(len(discovered_configurations), day))

    return discovered_configurations


def fetch_files(configuration: catalog.Configuration) -> typing.List[catalog.File]:
    discovered_files: typing.List[catalog.File] = [
        form_configuration_file(
            configuration.address,
            file
        )
        for file in os.listdir(configuration.address)
        if os.path.isfile(os.path.join(configuration.address, file))
            and file.endswith(".nc")
    ]

    return discovered_files


if __name__ == "__main__":
    generated_catalog = get_catalog(sys.argv[1])
    print(generated_catalog)
