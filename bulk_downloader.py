# -*- coding: utf-8 -*-
# Copyright (c) 2022 LEEP - University of Exeter (UK)
# Mattia C. Mancini (m.c.mancini@exeter.ac.uk), September 2022
'''
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
'''
from chess.config import ChessConfig
from chess.chess_manager import download_chess

# Define arguments for download
rcps = ['rcp26', 'rcp45', 'rcp60', 'rcp85']
climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
ensembles = [1, 4, 6, 15]
config = ChessConfig('config.ini')

# Dowload the data
download_chess(config, rcps, climate_vars, ensembles, bias_corrected=True)
