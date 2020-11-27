#!/bin/env python
"""
Put module documentation here
"""

import os
import string

from datetime import datetime

import requests
from bs4 import BeautifulSoup

import NOMADSExplorer.explore.directory as directory


_NOMADS_ADDRESS = os.environ.get(
    "NOMADS_ADDRESS",
    "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/"
)
"""(:class:`str`) The address used to connect to a NOMADS-like structure"""

_DAY_FORMAT = "%Y%m%d"


def get_int_from_word(word: str) -> [None, int]:
    """
    Attempt to pull a combined integer out of a word

    :param word: The word to search through
    :return: An integer if the word contains numbers, None otherwise
    """
    individual_numbers = [character for character in word if character in string.digits]

    if len(individual_numbers) == 0:
        return None

    return int("".join(individual_numbers))


def extract_file_attributes(filename: str) -> dict:
    """
    Discover NWM attributes by looking through the file name

    Describes:
    * reference: The hour of the day in zulu time for when the forecast begins
    * configuration: The forecast configuration for the NWM, like 'short_range',
    * model_type: What the model was forecasting, like 'channel_rt'
    * member: The numerical identifier for the ensemble member IF the forecast was an ensemble
    * step: The relative step of the forecast values into the overall forecast (1 hour in, 2 hours in, etc)
    * area: Over where the forecast occured, like 'conus'

    :param filename: The name of the file to search
    :return: A dictionary containing values describing a NWM file's attributes
    """
    attributes = {
        "reference": None,
        "configuration": None,
        "model_type": None,
        "member": None,
        "step": None,
        "area": None
    }

    name_parts = filename.split(".")

    # Get the reference at index 1
    attributes["reference"] = int(name_parts[1][1:-1])

    # Get the configuration at index 2
    attributes["configuration"] = name_parts[2]

    # Get the model type at index 3; if it ends in a digit, that digit needs to end up as the member and
    # the member pattern needs to be filtered out
    model_type_and_member = name_parts[3]
    member = get_int_from_word(model_type_and_member)

    if member is not None:
        attributes["member"] = member
        model_type_and_member = model_type_and_member.replace("_" + str(member), "")

    attributes["model_type"] = model_type_and_member

    # Get the time step at index 4
    attributes["step"] = get_int_from_word(name_parts[4])

    # Get the area at index 5
    attributes["area"] = name_parts[5]

    return attributes


def form_configuration(address: str, link) -> directory.Configuration:
    """
    Form a Configuration object based on a parsed link

    :param address: The address for the page that contained this link
    :param link: The discovered link
    :return: A configuration object that may contain individual forecasts
    """
    member = get_int_from_word(link.text)
    if member is None:
        configuration = link.text
    else:
        configuration = link.text.replace("_mem" + str(member), "")

    return directory.Configuration(
        configuration_type=configuration.strip("/"),
        address=os.path.join(address, link['href']),
    )


def form_configuration_file(address: str, link) -> directory.File:
    """
    Creates metadata for files that belong to a configuration

    :param address: The address of the configuration
    :param link: The parsed link to the file
    :return: An object containing the metadata for the discovered file
    """
    attributes = extract_file_attributes(link.text)
    configuration_file = directory.File(
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


def get_directory(url: str = None, verbose: bool = False) -> directory.Directory:
    if url is None:
        url = _NOMADS_ADDRESS

    with requests.get(url) as response:
        if response.status_code >= 400:
            raise Exception("The web service hosting NWM data could not be reached. ({})".format(response.status_code))

        if verbose:
            print("Getting information about the latest forecasts")

        web_listing = BeautifulSoup(response.text, features="html.parser")

        if verbose:
            print("Information about the latest forecasts were found")

    directory_contents = directory.Directory(url)

    for link in web_listing.find_all("a"):
        if link.text.startswith("nwm"):
            date = datetime.strptime(link.text[4:-1], _DAY_FORMAT)
            directory_contents[date] = directory.Day(
                date=date,
                name=link.text.strip("/"),
                address=os.path.join(url, link['href'])
            )

    if verbose:
        print("{} forecast days were found".format(len(directory_contents)))

    # Change this to be multiprocessed
    for date, day in directory_contents.days.items():
        with requests.get(day.address) as response:
            web_listing = BeautifulSoup(response.text, features="html.parser")

        # Multiprocess or overkill?
        for configuration_entry in web_listing.find_all("a"):
            if configuration_entry.text == 'Parent Directory':
                continue

            day[configuration_entry.text.strip("/")] = form_configuration(
                day.address,
                configuration_entry
            )

        for configuration_name, configuration in day.configurations.items():  # type: str, directory.Configuration
            with requests.get(configuration.address) as response:
                web_listing = BeautifulSoup(response.text, features="html.parser")

            for file_link in web_listing.find_all("a"):
                if file_link.text.endswith(".nc"):
                    configuration[file_link.text] = form_configuration_file(
                        configuration.address,
                        file_link
                    )

    return directory_contents


if __name__ == "__main__":
    directory = get_directory()
    print(directory)
