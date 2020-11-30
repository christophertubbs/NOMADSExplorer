#!/bin/env python
"""
Provides classes representing the file system structure containing National Water Model data on NOMADS
"""

from datetime import datetime
import typing

import logging


class File(object):
    """
    Represents a file that may be retrieved from a National Water Model data set structured like NOMADS
    """

    __slots__ = [
        'name',
        'address',
        'reference',
        'type',
        'model_type',
        'step',
        'area',
        'member'
    ]

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
        :param address: Where the file is located
        :param reference: The reference time between 0 and 24
        :param configuration: The configuration of the model (short range, medium range, long range, etc)
        :param model_type: The type of model (channel_rt, reservoir, land, etc)
        :param step: The time step of the file for the model
        :param area: What area of land the data pertains to (CONUS, Hawaii, etc)
        :param member: If the model was an ensemble, the identifier for the member
        """
        self.name: str = name
        """(:class:`str`) The name of the file"""

        self.address: str = address
        """(:class:`str`) Where the file is located"""

        self.reference: int = reference
        """(:class:`int`) The reference time between 0 and 24"""

        self.type: str = configuration
        """(:class:`str`) The configuration of the model (short range, medium range, long range, etc)"""

        self.model_type: str = model_type
        """(:class:`str`) The type of model (channel_rt, reservoir, land, etc)"""

        self.step: int = step
        """(:class:`int`) The time step of the file for the model"""

        self.area: str = area
        """(:class:`str`) What area of land the data pertains to (CONUS, Hawaii, etc)"""

        self.member: int = member
        """(:class:`int`) If the model was an ensemble, the identifier for the member"""

    def __str__(self):
        return "{} ({})".format(self.name, self.address)

    def __repr__(self):
        return self.__str__()


class Configuration(object):
    """
    Represents a single configuration of the national water model
    """

    __slots__ = [
        'address',
        'type',
        'member',
        'files',
        'key_iterator',
        'loader_module',
        'day'
    ]

    def __init__(
            self,
            configuration_type: str,
            address: str,
            loader_module,
            day: "Day",
            member: int = None
    ):
        """
        Constructor

        :param configuration_type: The name of the configuration (long range, short range, etc)
        :param address: Where the collection of configuration data may be found either locally or remotely
        :param loader_module: What module will be used to load data
        :param day: The day that this configuration belongs to
        :param member: An optional identifier for an ensemble member
        """
        self.address: str = address
        """(:class:`str`) Where the collection of configuration data may be found either locally or remotely"""

        self.type: str = configuration_type
        """(:class:`str`) The name of the configuration (long range, short range, etc)"""

        self.member: typing.Union[None, int] = member
        """(:class:`int`) An optional identifier for an ensemble member"""

        self.files: typing.Dict[str, File] = dict()
        """(:class:`dict`) Files belonging to the given configuration"""

        self.key_iterator = None
        """An iterator across all keys of the files"""

        self.loader_module = loader_module
        """What module will be used to load data (`NOMADSExplorer.explore.local` or `NOMADSExplorer.explore.remote`)"""

        self.day = day
        """(:class:`Day`) The day that this configuration belongs to"""

    def _load_files(self):
        """
        Loads the collection of all files for this configuration
        """
        if self.files is None or len(self.files) == 0:
            self.files = {
                file.name: file
                for file in self.loader_module.fetch_files(self)
            }

    def all_files(self) -> typing.List[File]:
        if self.files is None or len(self.files) == 0:
            self._load_files()

        return list(self.files.values())

    def get_timeseries(self, model_type: str, reference: int) -> typing.List[File]:
        if self.files is None or len(self.files) == 0:
            self._load_files()

        return sorted(
            [file for file in self.files.values() if file.model_type == model_type and file.reference == reference],
            key=lambda file: file.step
        )

    def get_all_timeseries(self) -> typing.List["TimeSeries"]:
        if self.files is None or len(self.files) == 0:
            self._load_files()

        timeseries: typing.List["TimeSeries"] = list()

        # Partition contained files by the model type, then reference
        partitions: typing.Dict[str, typing.Dict[int, typing.List[File]]] = dict()

        for file in self.files.values():
            if file.model_type not in partitions:
                partitions[file.model_type] = dict()

            if file.reference not in partitions[file.model_type]:
                partitions[file.model_type][file.reference] = list()

            partitions[file.model_type][file.reference].append(file)

        for model_type, reference_files in partitions.items():
            for reference, files in reference_files.items():
                timeseries.append(
                    TimeSeries(
                        files,
                        reference,
                        self.type,
                        model_type,
                        files[0].area if files else None,
                        self.day,
                        self.member
                    )
                )

        return timeseries

    def __getitem__(self, item: str) -> [None, File]:
        if not isinstance(item, str):
            raise Exception("The key for a file in a configuration must be a string")

        if self.files is None or len(self.files) == 0:
            self._load_files()

        return self.files.get(item, None)

    def __setitem__(self, key: str, value: File):
        if not isinstance(key, str) and not isinstance(value, File):
            raise Exception("Value cannot be set on configuration; the key is not a string and the value is not a file")
        elif not isinstance(key, str):
            raise Exception("Value cannot be set on configuration; the key is not a string")
        elif not isinstance(value, File):
            raise Exception("Value cannot be set on configuration; the value is not a File")
        self.files[key] = value

    def __iter__(self):
        if self.files is None or len(self.files) == 0:
            self._load_files()

        self.key_iterator = iter(self.files)
        return self

    def __next__(self) -> (str, File):
        if self.files is None or len(self.files) == 0:
            self._load_files()

        if self.key_iterator is None:
            self.key_iterator = iter(self.files)

        # This will eventually raise a StopIteration, but we want that
        next_key = next(self.key_iterator)
        return next_key, self.files[next_key]

    def __len__(self) -> int:
        if self.files is None or len(self.files) == 0:
            self._load_files()

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
    """
    Represents a day's worth of forecasts and simulations
    """

    __slots__ = [
        'address',
        'name',
        'date',
        'configurations',
        'key_iterator',
        'loader_module'
    ]

    def __init__(self, date: datetime, name: str, address: str, loader_module):
        """
        Constructor

        :param date: The technical representation of the day
        :param name: The name of the day
        :param address:
        :param loader_module:
        """
        self.address: str = address
        self.name: str = name
        self.date: datetime = date
        self.configurations: typing.Dict[str, Configuration] = dict()
        self.key_iterator = None
        self.loader_module = loader_module

    def _load_configurations(self):
        """
        Loads all configurations available for this day
        """
        if self.configurations is None or len(self.configurations) == 0:
            self.configurations = {
                configuration.type: configuration
                for configuration in self.loader_module.fetch_configurations(self)
            }

    def get_date(self) -> str:
        """
        :return: The date in an easily readable format
        """
        return self.date.strftime("%Y-%m-%d")

    def __iter__(self):
        if self.configurations is None or len(self.configurations) == 0:
            self._load_configurations()

        self.key_iterator = iter(self.configurations)
        return self

    def __next__(self):
        if self.configurations is None or len(self.configurations) == 0:
            self._load_configurations()

        if self.key_iterator is None:
            self.key_iterator = iter(self.configurations)

        # This will eventually raise a StopIteration, but we want it to
        next_key = next(self.key_iterator)
        return next_key, self.configurations[next_key]

    def __getitem__(self, item: str) -> [None, Configuration]:
        if self.configurations is None or len(self.configurations) == 0:
            self._load_configurations()

        if not isinstance(item, str):
            raise Exception("The key for a configuration must be a string")

        return self.configurations.get(item, None)

    def __setitem__(self, key: str, value: Configuration):
        if not isinstance(key, str) and not isinstance(value, Configuration):
            raise Exception("Value cannot be set on Day; the key is not a string and the value is not a Configuration")
        elif not isinstance(key, str):
            raise Exception("Value cannot be set on Day; the key is not a string")
        elif not isinstance(value, Configuration):
            raise Exception("Value cannot be set on Day; the value is not a Configuration")
        self.configurations[key] = value

    def __len__(self) -> int:
        if self.configurations is None or len(self.configurations) == 0:
            self._load_configurations()

        return len(self.configurations)

    def __str__(self):
        return "{} (Configurations = {})".format(self.date, len(self.configurations))

    def __repr__(self):
        return self.__str__()


class Catalog(object):
    """
    Represents a catalog of all available National Water Model forecasts and simulations
    available at the specified location
    """

    __slots__ = [
        'address',
        'days',
        'key_iterator',
        'loader_module'
    ]

    def __init__(self, address: str, loader_module):
        """
        Constructor

        :param address: The location of the root of the catalog
        :param loader_module: What module will load the contained data (`NOMADSExplorer.explore.web` or `NOMADSExplorer.explorer.local`)
        """
        self.address: str = address
        """(:class:`str`) The location of the root of the catalog"""

        self.days: typing.Dict[datetime, Day] = dict()
        """All days of forecasts and simulations available within the catalog"""

        self.key_iterator = None
        """An internal iterator over all contained days"""

        self.loader_module = loader_module
        """What module will load the contained data (`NOMADSExplorer.explore.web` or `NOMADSExplorer.explorer.local`)"""

    def get_all_timeseries(self, configuration_type: str, model_type: str) -> typing.List["TimeSeries"]:
        """
        Retrieves all time series across all days for the given configuration and model type

        :param configuration_type: The name of the configuration of the model (short_range, analysis_assim, etc)
        :param model_type: The type of model run (channel_rt, land, reservoir, etc)
        :return: A list of all matching time series in the catalog
        """
        timeseries: typing.List["TimeSeries"] = list()

        for day in self.days.values():
            configuration = day[configuration_type]
            timeseries.extend(
                series
                for series in configuration.get_all_timeseries()
                if series.model_type.lower() == model_type.lower()
            )

        return timeseries

    def __len__(self):
        return len(self.days)

    def __iter__(self):
        self.key_iterator = iter(self.days)
        return self

    def __next__(self) -> (datetime, Day):
        if self.key_iterator is None:
            self.key_iterator = iter(self.days)

        # This will eventually raise a StopIteration, but we want it to
        next_key = next(self.key_iterator)
        return next_key, self.days[next_key]

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


class TimeSeries(object):
    """
    Represents all files making up a time series
    """
    def __init__(
            self,
            files: typing.List[File],
            reference: int,
            configuration: str,
            model_type: str,
            area: str,
            day: Day,
            member: int = None
    ):
        """
        Constructor

        :param files: All files available to make up this time series
        :param reference: The hour 0 through 23 of when the forecast begins
        :param configuration: The configuration of the model (short_range, analysis_assim, etc)
        :param model_type: What model was run (channel_rt, land, reservoir, etc)
        :param area: Over what span of land that the forecast pertains to (CONUS, Hawaii, etc)
        :param day: The day when the forecast began
        :param member: The identifier for the ensemble member if the time series is part of an ensemble
        """
        self.files = sorted(files, key=lambda file: file.step)
        """(:class:`list`) All files available to make up this time series"""

        self.reference = reference
        """(:class:`int`) The hour 0 through 23 of when the forecast begins"""

        self.configuration = configuration
        """(:class:`str`) The configuration of the model (short_range, analysis_assim, etc)"""

        self.model_type = model_type
        """(:class:`str`) What model was run (channel_rt, land, reservoir, etc)"""

        self.area = area
        """(:class:`str`) Over what span of land that the forecast pertains to (CONUS, Hawaii, etc)"""

        self.member = member
        """(:class:`int`) The identifier for the ensemble member if the time series is part of an ensemble"""

        self.day = day
        """(:class:`Day`) The day when the forecast began"""

        self.file_iterator = None
        """An internal iterator across all files"""

    def __iter__(self):
        self.file_iterator = iter(self.files)
        return self

    def __next__(self):
        if self.file_iterator is None:
            self.file_iterator = iter(self.files)

        return next(self.file_iterator)

    def __str__(self):
        string = "{} {} over {} at t{}Z on {}".format(
            self.configuration,
            self.model_type,
            self.area,
            str(self.reference).zfill(2),
            self.day.get_date()
        )

        if self.member is not None:
            string += ", ensemble member {}".format(self.member)

        string += " (Steps = {})".format(len(self.files))
        return string

    def __repr__(self):
        return str(self)
