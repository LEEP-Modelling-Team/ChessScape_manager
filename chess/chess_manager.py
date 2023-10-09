# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP - University of Exeter (UK)
# Mattia C. Mancini (m.c.mancini@exeter.ac.uk), September 2022
"""
chess_manager.py
================

Various utility functions to download and process the ChessScape climate data.

Functions available:
    - download_chess: Download the ChessScape data from ftp. Requires an account
      with CEDA with authorisation to use their FTP services. For info:
      https://help.ceda.ac.uk/article/280-ftp
    
"""
import ftplib
import os
from os import listdir
from os.path import isfile, join
import re

# pylint: disable=R0914
# pylint: disable=R1702
def download_chess(config, rcps, climate_vars, ensembles, bias_corrected):
    '''
    FTP download of ChessScape data, which is then
    saved into a specified directory
    :param config: a ChessConfig instance reading the relevant configuration
           parameters. See chess.config.py for more info
    :param rcps: a list of strings defining the rcp scenarios required for donwload
           (e.g.: ['rcp26', 'rcp45', 'rcp60', 'rcp85']). Refer to the ChessScape
           documentation for information on the data available
    :param climate_vars: a list of climate variables to be downloaded. 
           (e.g.): ['tas', 'hurs', 'tasmin', 'tasmax'], Refer to the
           ChessScape data documentation for the variables available for download
    :param ensembles: list of integers defining the climate ensemble members to be downloaded.
           There are 4 available: [1, 4, 6, 15]. More info in the docs for 
           the ChessScape data.
    :param bias_corrected: Whether the data to be downloaded has been bias corrected or not.
           Refer to the ChessScape data documentation: the available
           climate_vars depend on whether the data has been bias corrected or not!
    '''
    ddir = config.data_dirs['ceda_dir']
    user = config.ceda_parameters['ceda_usr']
    pwd = config.ceda_parameters['ceda_pwd']
    ftp_addr = config.ceda_parameters['ftp_address']

    if not os.path.isdir(ddir):
        os.mkdir(ddir)
        print('Download data directory successfully created!')

    # Change the local directory to where you want to put the data
    os.chdir(ddir)

    # login to CEDA FTP
    f = ftplib.FTP(ftp_addr, user, pwd)

    # loop through RCPs
    for rcp in rcps:

        # loop through enselmbles
        for ensemble in ensembles:

            # loop through weather variables
            for var in climate_vars:

                # loop through years
                for year in range(2020,2081):

                    # loop through months
                    for month in range(1,13):
                        if bias_corrected:
                            filedir = (
                                f"/badc/deposited2021/chess-scape/data/{rcp}"
                                f"_bias-corrected/{ensemble:02d}/daily/{var}/"
                            )
                            f.cwd(filedir)
                            file = (
                                f"chess-scape_{rcp}_bias-corrected_{ensemble:02d}"
                                f"_{var}_uk_1km_daily_{year:04d}{month:02d}01-"
                                f"{year:04d}{month:02d}30.nc"
                            )
                        else:
                            filedir = (
                                f"/badc/deposited2021/chess-scape/data/{rcp}"
                                f"/{ensemble:02d}/daily/{var}/"
                            )
                            f.cwd(filedir)
                            file = (
                                f"chess-scape_{rcp}_"
                                f"{ensemble:02d}_{var}_uk_1km_daily_{year:04d}"
                                f"{month:02d}01-{year:04d}{month:02d}30.nc"
                            )
                        try:
                            with open(file, "wb") as local_file:
                                f.retrbinary(f"RETR {file}", local_file.write)
                            print(f'Downloading file {file}...')
                        except FileNotFoundError:
                            print(f'file {file} not found. Skipping...')
                            continue

    print('All files successfully downloaded')
    # Close FTP connection
    f.close()
# pylint: enable=R0914
# pylint: enable=R1702

# List all ChessScape files within path for the selected rcp, years, climate_vars and ensembles
def filter_files(rcp, years, climate_vars, ensembles, path):
    '''
    Identifies all files in ceda download dir. containing years and climate_vars for the 
    specified ensembles and rcps. Years and climate_vars can be one or more. In
    both cases, they must be passed as lists
    '''
    if not isinstance(years, list):
        years = [years]
    if not isinstance(climate_vars, list):
        climate_vars = [climate_vars]
    if not isinstance(ensembles, list):
        ensembles = [ensembles]
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    df = [re.split(r'_|\.|-', elem) for elem in allfiles]

    filter_list = [False for x in range(len(df))]
    for year in years:
        for var in climate_vars:
            for ensemble in ensembles:
                for i, _ in enumerate(df):
                    yr = int(df[i][10][0:4])
                    if str(ensemble) in df[i][5] and \
                        rcp in df[i][2] and \
                        var == df[i][6] and \
                        yr == year:
                        filter_list[i] = True
                    else:
                        continue
    filtered_files = [i for (i, v) in zip(allfiles, filter_list) if v]
    filtered_files = [path + '\\' + x for x in filtered_files]
    return filtered_files

class BNGError(Exception):
    """Exception raised by bng.py module"""

def _init_regions_and_offsets():
    # Region codes for 100 km grid squares.
    regions = [['HL', 'HM', 'HN', 'HO', 'HP', 'JL', 'JM'],
               ['HQ', 'HR', 'HS', 'HT', 'HU', 'JQ', 'JR'],
               ['HV', 'HW', 'HX', 'HY', 'HZ', 'JV', 'JW'],
               ['NA', 'NB', 'NC', 'ND', 'NE', 'OA', 'OB'],
               ['NF', 'NG', 'NH', 'NJ', 'NK', 'OF', 'OG'],
               ['NL', 'NM', 'NN', 'NO', 'NP', 'OL', 'OM'],
               ['NQ', 'NR', 'NS', 'NT', 'NU', 'OQ', 'OR'],
               ['NV', 'NW', 'NX', 'NY', 'NZ', 'OV', 'OW'],
               ['SA', 'SB', 'SC', 'SD', 'SE', 'TA', 'TB'],
               ['SF', 'SG', 'SH', 'SJ', 'SK', 'TF', 'TG'],
               ['SL', 'SM', 'SN', 'SO', 'SP', 'TL', 'TM'],
               ['SQ', 'SR', 'SS', 'ST', 'SU', 'TQ', 'TR'],
               ['SV', 'SW', 'SX', 'SY', 'SZ', 'TV', 'TW']]

    # Transpose so that index corresponds to offset
    regions = list(zip(*regions[::-1]))

    # Create mapping to access offsets from region codes
    offset_map = {}
    for i, row in enumerate(regions):
        for j, region in enumerate(row):
            offset_map[region] = (1e5 * i, 1e5 * j)

    return regions, offset_map

_regions, _offset_map = _init_regions_and_offsets()

# pylint: disable=R0914
def osgrid2bbox(gridref, os_cellsize):
    """
    Convert British National Grid references to OSGB36 numeric coordinates.
    of the bounding box of the 10km grid or 100km grid squares.
    Grid references can be 2, 4, 6, 8 or 10 figures.

    :param gridref: str - BNG grid reference
    :returns coords: dictionary {xmin, xmax, ymin, ymax}

    Examples:

    Single value
    >>> osgrid2bbox('NT2755072950', '10km')
    {'xmin': 320000, 'xmax': 330000, 'ymin': 670000, 'ymax': 680000}

    For multiple values, use Python's zip function and list comprehension
    >>> gridrefs = ['HU431392', 'SJ637560', 'TV374354']
    >>> [osgrid2bbox(g, '10km') for g in gridrefs]
    >>> [{'xmin': 440000, 'xmax': 450000, 'ymin': 1130000, 'ymax': 1140000}, 
        {'xmin': 360000, 'xmax': 370000, 'ymin': 330000, 'ymax': 340000}, 
        {'xmin': 530000, 'xmax': 540000, 'ymin': 70000, 'ymax': 80000}]
    """
    # Validate input
    bad_input_message = (
        f"Valid gridref inputs are 2 characters and none, 2, 4, 6, 8"
        f" or 10-fig references as strings "
        f"e.g. \"NN123321\", or lists/tuples/arrays of strings. "
        f"[{gridref}]"
    )

    gridref = gridref.upper()
    if os_cellsize == '10km':
        try:
            pattern = r'^([A-Z]{2})(\d{2}|\d{4}|\d{6}|\d{8}|\d{10})$'
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region, coords = match.groups()
        except (TypeError, AttributeError) as exc:
            # Non-string values will throw error
            raise BNGError(bad_input_message) from exc
    elif os_cellsize == '100km':
        try:
            pattern = r'^([A-Z]{2})'
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region = match.groups()[0]
        except (TypeError, AttributeError) as exc:
            raise BNGError(bad_input_message) from exc
    else:
        raise BNGError(
            "Invalid argument \'os_cellsize\' supplied:" 
            "values can only be \'10km\' or \'100km\'"
        )

    # Get offset from region
    try:
        x_offset, y_offset = _offset_map[region]
    except KeyError as exc:
        raise BNGError(f"Invalid grid square code: {region}") from exc

    # Get easting and northing from text and convert to coords
    if os_cellsize == '10km':
        coords = coords[0:2] # bbox is for each 10km cell!
        half_figs = len(coords) // 2
        easting, northing = int(coords[:half_figs]), int(coords[half_figs:])
        scale_factor = 10 ** (5 - half_figs)
        x_min = int(easting * scale_factor + x_offset)
        y_min = int(northing * scale_factor + y_offset)
        x_max = int(easting * scale_factor + x_offset + 1e4)
        y_max = int(northing * scale_factor + y_offset + 1e4)
    elif os_cellsize == '100km':
        x_min = int(x_offset)
        y_min = int(y_offset)
        x_max = int(x_offset + 1e5)
        y_max = int(y_offset + 1e5)
    else:
        raise BNGError(
            "Invalid argument \'os_cellsize\' supplied: "
            "values can only be \'10km\' or \'100km\'"
        )

    return {
        'xmin': x_min,
        'xmax': x_max,
        'ymin': y_min,
        'ymax': y_max
    }
# pylint: enable=R0914

# pylint: disable=R0913
def print_progress_bar(
        iteration,
        total,
        prefix = '',
        suffix = '',
        decimals = 1,
        length = 100,
        fill = '█',
        print_end = "\r"
    ):
    """
    Progress bar from:
    https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    progress_bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{progress_bar}| {percent}% {suffix}', end = print_end)
    # Print New Line on Complete
    if iteration == total:
        print()
# pylint: enable=R0914
# pylint: enable=R0913
