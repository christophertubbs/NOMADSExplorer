#!/bin/env python
"""
Put module documentation here
"""

import os
import string

from datetime import datetime

import requests
from bs4 import BeautifulSoup


_NOMADS_ADDRESS = os.environ.get("NOMADS_ADDRESS", "https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/prod/")
"""(:class:`str`) The address used to connect to a NOMADS-like structure"""

_DAY_FORMAT = "%Y%m%d"


def get_int_from_word(word: str) -> [None, int]:
    individual_numbers = [character for character in word if character in string.digits]

    if len(individual_numbers) == 0:
        return None

    return int("".join(individual_numbers))


def extract_file_attributes(filename: str) -> dict:
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


def form_configuration(address: str, link) -> dict:
    member = get_int_from_word(link.text)
    if member is None:
        configuration = link.text
    else:
        configuration = link.text.replace("_mem" + str(member), "")

    return {
        "link": os.path.join(address, link["href"]),
        "type": configuration.strip("/"),
        "member": member,
        "files": dict()
    }


def form_configuration_file(address: str, link) -> dict:
    configuration_file = {
        "name": link.text,
        "link": os.path.join(address, link["href"])
    }
    attributes = extract_file_attributes(link.text)
    configuration_file.update(attributes)
    return configuration_file


# TODO: Return a directory object instead of a dictionary
def get_directory(url: str = None) -> dict:
    if url is None:
        url = _NOMADS_ADDRESS

    with requests.get(url) as response:
        web_listing = BeautifulSoup(response.text, features="html.parser")

    links = {
        datetime.strptime(link.text[4:-1], _DAY_FORMAT): {
            "name": link.text.strip("/"),
            "date": datetime.strptime(link.text[4:-1], _DAY_FORMAT),
            "link": os.path.join(url, link["href"]),
            "configurations": dict()
        }
        for link in web_listing.find_all("a")
        if link.text.startswith("nwm")
    }

    for link_key in links:  # type: str
        address = links[link_key]["link"]

        with requests.get(address) as response:
            web_listing = BeautifulSoup(response.text, features="html.parser")

        links[link_key]["configurations"] = {
            configuration_entry.text.strip("/"): form_configuration(address, configuration_entry)
            for configuration_entry in web_listing.find_all("a")
            if configuration_entry.text != 'Parent Directory'
        }

        for configuration in links[link_key]["configurations"].values():  # type: dict
            with requests.get(configuration["link"]) as response:
                web_listing = BeautifulSoup(response.text, features="html.parser")

            configuration["files"] = {
                file_link.text: form_configuration_file(configuration["link"], file_link)
                for file_link in web_listing.find_all("a")
                if file_link.text.endswith(".nc")
            }

    return links
