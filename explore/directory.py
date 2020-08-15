#!/bin/env python
"""
Provides classes representing the file system structure containing National Water Model data on NOMADS
"""

from datetime import datetime
import typing


class File(object):
    """
    Represents a file that may be retrieved from a National Water Model data set structured like NOMADS
    """
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
        """
        Constructor

        :param name: The name of the file
        :param address: The address of the file
        :param reference: The reference time between 0 and 24
        :param configuration: The configuration of the model (short range, medium range, long range, etc)
        :param model_type: The type of model (channel_rt, reservoir, land, etc)
        :param step: The time step of the file for the model
        :param area: What area of land the data pertains to (CONUS, Hawaii, etc)
        :param member: If the model was an ensemble, the identifier for the member
        """
        self.name: str = name
        self.address: str = address
        self.reference: int = reference
        self.type: str = configuration
        self.model_type: str = model_type
        self.step: int = step
        self.area: str = area
        self.member: int = member

    def __str__(self):
        return "{} ({})".format(self.name, self.address)

    def __repr__(self):
        return self.__str__()


class Configuration(object):
    def __init__(self, configuration_type: str, address: str, member: int = None):
        self.address: str = address
        self.type: str = configuration_type
        self.member: typing.Union[None, int] = member
        self.files: typing.Dict[str, File] = dict()

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

    def select_files(self, boolean_function: typing.Callable):
        new_configuration = Configuration(self.type, self.address, self.member)
        for file in self.files.values():
            if boolean_function(file):
                new_configuration.add_file(file)
        return new_configuration

    def all_files(self) -> typing.List[File]:
        return list(self.files.values())

    def get_timeseries(self, model_type: str, reference: int) -> typing.List[File]:
        return sorted(
            [file for file in self.files.values() if file.model_type == model_type and file.reference == reference],
            key=lambda file: file.step
        )

    def __getitem__(self, item: str) -> [None, File]:
        if not isinstance(item, str):
            raise Exception("The key for a file in a configuration must be a string")
        return self.files.get(item, None)

    def __setitem__(self, key: str, value: File):
        if not isinstance(key, str) and not isinstance(value, File):
            raise Exception("Value cannot be set on configuration; the key is not a string and the value is not a file")
        elif not isinstance(key, str):
            raise Exception("Value cannot be set on configuration; the key is not a string")
        elif not isinstance(value, File):
            raise Exception("Value cannot be set on configuration; the value is not a File")
        self.files[key] = value

    def __len__(self) -> int:
        return len(self.files)

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
        self.address: str = address
        self.name: str = name
        self.date: datetime = date
        self.configurations: typing.Dict[str, Configuration] = dict()

    def add_configuration(self, configuration: Configuration):
        self.configurations[configuration.type] = configuration

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
            for configuration in self.configurations.values()
            if configuration_type is None or configuration.type == configuration_type
        ])

    def get_timeseries(self, configuration_type: str, model_type: str, reference: int) -> typing.List[File]:
        configuration = self.configurations.get(configuration_type, None)  # type: [None, Configuration]

        if configuration is None:
            return list()
        else:
            return configuration.get_timeseries(model_type, reference)

    def select_files(self, boolean_function: typing.Callable):
        new_day = Day(self.date, self.name, self.address)
        for configuration in self.configurations.values():
            new_configuration = configuration.select_files(boolean_function)
            if len(new_configuration) > 0:
                new_day.add_configuration(new_configuration)
        return new_day

    def select_configurations(self, boolean_function: typing.Callable):
        new_day = Day(self.date, self.name, self.address)
        for configuration in self.configurations.values():
            if boolean_function(configuration):
                new_day.add_configuration(configuration)
        return new_day

    def all_files(self) -> typing.List[File]:
        total = list()

        for configuration in self.configurations.values():
            total.extend(configuration.all_files())

        return total

    def __getitem__(self, item: str) -> [None, Configuration]:
        if not isinstance(item, str):
            raise Exception("The key for a configuration must be a string")
        return self.configurations.get(item, None)

    def __setitem__(self, key: str, value: Configuration):
        if not isinstance(key, str) and not isinstance(value, Configuration):
            raise Exception("Value cannot be set on Day; the key is not a string and the value is not a Configuration")
        elif not isinstance(key, str):
            raise Exception("Value cannot be set on Day; the key is not a string")
        elif not isinstance(value, File):
            raise Exception("Value cannot be set on Day; the value is not a Configuration")
        self.configurations[key] = value

    def __len__(self) -> int:
        return len(self.configurations)

    def __str__(self):
        return "{} (Configurations = {})".format(self.date, len(self.configurations))

    def __repr__(self):
        return self.__str__()


class Directory(object):
    def __init__(self, address: str):
        self.address: str = address
        self.days: typing.Dict[datetime, Day] = dict()

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
            for day in self.days.values()
            if date is None or day.date == date
        ])

    def select_days(self, boolean_function: typing.Callable):
        new_directory = Directory(self.address)
        for day in self.days.values():
            if boolean_function(day):
                new_directory.add_day(day)
        return new_directory

    def select_files(self, boolean_function: typing.Callable):
        new_directory = Directory(self.address)
        for day in self.days.values():
            new_day = day.select_files(boolean_function)
            if len(new_day) > 0:
                new_directory.add_day(new_day)
        return new_directory

    def select_configurations(self, boolean_function: typing.Callable):
        new_directory = Directory(self.address)
        for day in self.days.values():
            new_day = day.select_configurations(boolean_function)
            if len(new_day) > 0:
                new_directory.add_day(new_day)
        return new_directory

    def all_files(self) -> typing.List[File]:
        total = list()
        for day in self.days.values():
            total.extend(day.all_files())
        return total

    def get_timeseries(self, date: datetime, configuration_type: str, model_type: str, reference: int) -> typing.List[File]:
        day = self.days.get(date, None)  # type: [None, Day]

        if day is None:
            return list()
        else:
            return day.get_timeseries(configuration_type, model_type, reference)

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

    def __str__(self):
        return "{} (Days = {})".format(self.address, len(self.days))

    def __repr__(self):
        return self.__str__()
