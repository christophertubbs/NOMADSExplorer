#!/bin/env python


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
