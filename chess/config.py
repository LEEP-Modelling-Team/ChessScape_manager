# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP - University of Exeter (UK)
# Mattia C. Mancini (m.c.mancini@exeter.ac.uk), September 2023
"""
Read an ini config file storing all the necessary variables
and parameters download the ChessScape climate data
"""

import configparser
import os

class ChessConfig:
    """
    Class to parse and format a configuration file containing all 
    the necessary parameters to download the ChessScape climate data
    """
    def __init__(self, config_file_path):
        self._get_config(config_file_path)

    def _get_config(self, config_file_path):
        """
        Parse items from the config.ini file
        """
        config = configparser.ConfigParser()
        config.read(config_file_path)
        for section_name in config.sections():
            section = config[section_name]
            section_dict = {key: os.path.expandvars(value) for key, value in section.items()}
            setattr(self, section_name, section_dict)

    def __str__(self):
        """
        Format and return a string representation of the ChessConfig object
        """
        result = ""
        for section_name in dir(self):
            if not callable(getattr(self, section_name)) and not section_name.startswith("__"):
                result += f"[{section_name}]\n"
                section = getattr(self, section_name)
                for key, value in section.items():
                    result += f"{key} = {value}\n"
        return result
