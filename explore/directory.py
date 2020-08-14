#!/bin/env python
"""
Put module documentation here
"""

from datetime import datetime


class File(object):
    def __init__(
            self,
            name: str,
            address: str,
            reference: int,
            configuration: str,
            model_type: str,
            step: int,
            area: str,
            member: int = None
    ):
        self.name = name
        self.address = address
        self.reference = reference
        self.type = configuration
        self.model_type = model_type
        self.step = step
        self.area = area
        self.member = member

    def __str__(self):
        return "{} ({})".format(self.name, self.address)

    def __repr__(self):
        return self.__str__()


class Configuration(object):
    def __init__(self, configuration_type: str, address: str, member: int = None):
        self.address = address
        self.type = configuration_type
        self.member = member
        self.files = dict()

    def add_file(self, file: File):
        self.files[file.name] = file

    def get_file_count(
            self,
            name: str = None,
            reference: int = None,
            model_type: str = None,
            step: int = None,
            area: str = None,
            member: int = None
    ):
        return len([
            file
            for file in self.files.values()
            if (name is None or file.name == name) and
               (reference is None or file.reference == reference) and
               (model_type is None or file.model_type == model_type) and
               (step is None or file.step == step) and
               (area is None or file.area == area) and
               (member is None or file.member == member)
        ])

    # TODO: Implement drop/filter functions

    # TODO: Implement __getitem__
    # TODO: Implement __setitem__
    # TODO: Implement __len__

    def __str__(self):
        description = self.type

        if self.member is not None:
            description += ", Member " + str(self.member)

        description += "(files = {})".format(len(self.files))
        return description

    def __repr__(self):
        return self.__str__()


class Day(object):
    def __init__(self, date: datetime, name: str, address: str):
        self.address = address
        self.name = name
        self.date = date
        self.configurations = dict()

    def add_configuration(self, configuration: Configuration):
        self.configurations[configuration.type] = Configuration

    def get_file_count(
            self,
            name: str = None,
            reference: int = None,
            configuration_type: str = None,
            model_type: str = None,
            step: int = None,
            area: str = None,
            member: int = None
    ):
        return sum([
            configuration.get_file_count(
                name=name,
                reference=reference,
                model_type=model_type,
                step=step,
                area=area,
                member=member
            )
            for configuration in self.configurations
            if configuration_type is None or configuration.type == configuration_type
        ])

    # TODO: Implement drop/filter functions

    # TODO: Implement __getitem__
    # TODO: Implement __setitem__
    # TODO: Implement __len__

    def __str__(self):
        return "{} (Configurations = {})".format(self.date, len(self.configurations))

    def __repr__(self):
        return self.__str__()


class Directory(object):
    def __init__(self, address: str):
        self.address = address
        self.days = dict()

    def add_day(self, day: Day):
        self.days[day.date] = day

    def get_file_count(
            self,
            name: str = None,
            reference: int = None,
            configuration_type: str = None,
            date: datetime = None,
            model_type: str = None,
            step: int = None,
            area: str = None,
            member: int = None
    ):
        return sum([
            day.get_file_count(
                name=name,
                reference=reference,
                model_type=model_type,
                configuration_type=configuration_type,
                step=step,
                area=area,
                member=member
            )
            for day in self.days
            if date is None or day.date == date
        ])

    def __len__(self):
        return len(self.days)

    def __getitem__(self, key: datetime):
        if not isinstance(key, datetime):
            raise Exception("The key for items in a directory must be a date and time")

        return self.days.get(key, None)

    def __setitem__(self, key: datetime, value: Day):
        if not isinstance(key, datetime) and not isinstance(value, Day):
            raise Exception(
                "The key for the directory must be a date and time and the value must be a Day; "
                "neither are true"
            )
        elif not isinstance(key, datetime):
            raise Exception("The key in a directory must be a date and time")
        elif not isinstance(value, Day):
            raise Exception("The value in a directory must be a Day")

        self.days[key] = value

    # TODO: Implement drop/filter functions

    def __str__(self):
        return "{} (Days = {})".format(self.address, len(self.days))

    def __repr__(self):
        return self.__str__()
