# -*- coding: utf-8 -*-
# Copyright (c) 2022 LEEP - University of Exeter (UK)
# Mattia C. Mancini (m.c.mancini@exeter.ac.uk), September 2022
"""
CHESS-SCAPE data downloader.
============================

Script that downloads climate data from the CEDA archive and saves it on disk
It requires a CEDA account, and the data is downloaded through ftp. 
Credentials to access CEDA are stored as environment variables and
loaded using the ChessConfig class (see chess.config.py for more info).
Data directories and user configuration parameters are stored in the
'config.ini' file. Make sure to set the appropriate environment variables
and directories before running the script

CHESS-SCAPE data downloaded from this address:
https://catalogue.ceda.ac.uk/uuid/8194b416cbee482b89e0dfbe17c5786c

- The following RCPs are included: 'rcp26', 'rcp45', 'rcp60', 'rcp85'
- The following variables are included: 'tas', 'tasmax', 'tasmin', 'pr', 
  'rlds', 'rsds', 'hurs', 'sfcWind'
- A year is defined as 12 months of 30 days each
- Each RCP contains four ensemble members (01, 02, 03, 04); member 01 is the 
  default parameterisation of the Hadley Centre Climate model and the others 
  provide an estimate of climate model uncertainty
- Data can be bias corrected or not, which is specified by the 'bias_corrected'
  parameter
-------------------------------------------------------------------------------
USE
The donwload_chess function requires a single argument 'config', which is an instance
of the configuration parser.
By default, the script will retrieve data as follows:
    - from year 1980 to year 2080
    - for RCPs 2.6, 4.5, 6.0, 8.5
    - For ensemble members 1, 4, 6, 15
    - for the following climate variables: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 
      'rsds', 'hurs', 
      'sfcWind'

If a user wishes to download differet data, optional parameters must be passed as follows:
    :param 'rcps': a list of any of 'rcp26', 'rcp45', 'rcp60', 'rcp85'
    :param 'start_year': any year in the interval 1980-2080
    :param 'end_year': any year in the interval 1980-2080
    :param 'climate_vars': a list of any of the ChessScape climate variables
           (make sure they exist for the selected data: bias-corrected data does not have the
           same variables as the non bias corrected data). Example climate variables: 
           'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind'
    :param 'ensembles': a list of any of 1, 4, 6, 15 

Example default use:
    >>> config = ChessConfig("config.ini")
    >>> download_chess(config)

Example custom use only retrieving RCPs 2.6 and 4.5 for 2020-2050:
    >>> config = ChessConfig("config.ini")
    >>> download_chess(config, rcps=['rcp26', 'rcp45'], start_year=2020, end_year=2050)

Example custom use only retrieving avg. temperature and precipitation:
    >>> config = ChessConfig("config.ini")
    >>> download_chess(config, climate_vars=['tas', 'pr']
"""

from chess.config import ChessConfig
from chess.chess_manager import download_chess

config = ChessConfig("config.ini")
download_chess(config)
