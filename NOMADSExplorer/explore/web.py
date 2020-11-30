#!/bin/env python
"""
Functions for retrieving National Water Model data through a remote network
"""

import sys
import os
import typing
import logging

from datetime import datetime

import requests
from bs4 import BeautifulSoup

import NOMADSExplorer.explore.catalog as catalog
import NOMADSExplorer.common as common

# Try to use lxml for html parsing; if it's not there, fall back to the standard
try:
    import lxml
    HTML_PARSER = 'lxml'
except ImportError:
    logging.warn("lxml is not installed; falling back to the standard html parser for remote exploration")
    HTML_PARSER = 'html.parser'


_NOMADS_ADDRESS = os.environ.get(
    "NOMADS_ADDRESS",
    "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/"
)
"""(:class:`str`) The address used to connect to a NOMADS-like structure"""

_DAY_FORMAT = "%Y%m%d"

LOADER_MODULE = sys.modules[__name__]


def form_configuration(day: catalog.Day, address: str, link) -> catalog.Configuration:
    """
    Form a Configuration object based on a parsed link

    :param day: The day of which this configuration coincides
    :param address: The address for the page that contained this link
    :param link: The discovered link
    :return: A configuration object that may contain individual forecasts
    """
    member = common.get_int_from_word(link.text)
    if member is None:
        configuration = link.text
    else:
        configuration = link.text.replace("_mem" + str(member), "")

    return catalog.Configuration(
        configuration_type=configuration.strip("/"),
        address=os.path.join(address, link['href']),
        loader_module=LOADER_MODULE,
        day=day
    )


def form_configuration_file(address: str, link) -> catalog.File:
    """
    Creates metadata for files that belong to a configuration

    :param address: The address of the configuration
    :param link: The parsed link to the file
    :return: An object containing the metadata for the discovered file
    """
    attributes = common.extract_file_attributes(link.text)
    configuration_file = catalog.File(
        name=link.text,
        address=os.path.join(address, link['href']),
        reference=attributes['reference'],
        configuration=attributes['configuration'],
        model_type=attributes['model_type'],
        step=attributes['step'],
        area=attributes['area'],
        member=attributes.get("member")
    )
    return configuration_file


def get_catalog(url: str = None) -> catalog.Catalog:
    """
    Create a catalog for the given url

    :param url: The url to use. If not given, NOMADS will be used
    :return: A catalog that will help explore National Water Model data at the given url
    """
    if url is None:
        url = _NOMADS_ADDRESS

    with requests.get(url) as response:
        if response.status_code >= 400:
            raise Exception("The web service hosting NWM data could not be reached. ({})".format(response.status_code))

        logging.debug("Getting information about the latest forecasts or simulations for a new catalog")

        web_listing = BeautifulSoup(response.text, features=HTML_PARSER)

        logging.debug("Information about the latest forecasts were found for a new catalog")

    catalog_contents = catalog.Catalog(url, loader_module=LOADER_MODULE)

    for link in web_listing.find_all("a"):
        if link.text.startswith("nwm"):
            date = datetime.strptime(link.text[4:-1], _DAY_FORMAT)
            catalog_contents[date] = catalog.Day(
                date=date,
                name=link.text.strip("/"),
                address=os.path.join(url, link['href']),
                loader_module=LOADER_MODULE
            )

    logging.debug("{} forecast days were found for a new catalog".format(len(catalog_contents)))

    return catalog_contents


def fetch_configurations(day: catalog.Day) -> typing.List[catalog.Configuration]:
    discovered_configurations: typing.List[catalog.Configuration] = list()

    logging.debug("Getting configurations for {}".format(day))

    with requests.get(day.address) as response:
        web_listing = BeautifulSoup(response.text, features=HTML_PARSER)

    for configuration_entry in web_listing.find_all("a"):
        if configuration_entry.text == 'Parent Directory':
            continue

        discovered_configurations.append(
            form_configuration(
                day,
                day.address,
                configuration_entry
            )
        )

    logging.debug("{} configurations found for {}".format(len(discovered_configurations), day))

    return discovered_configurations


def fetch_files(configuration: catalog.Configuration) -> typing.List[catalog.File]:
    discovered_files: typing.List[catalog.File] = list()

    with requests.get(configuration.address) as response:
        web_listing = BeautifulSoup(response.text, features=HTML_PARSER)

    for file_link in web_listing.find_all("a"):
        if file_link.text.endswith(".nc"):
            discovered_files.append(
                form_configuration_file(
                    configuration.address,
                    file_link
                )
            )

    return discovered_files


if __name__ == "__main__":
    generated_catalog = get_catalog()
    print(generated_catalog)
