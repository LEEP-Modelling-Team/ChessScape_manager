# -*- coding: utf-8 -*-
# Copyright (c) 2022 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), November 2022
# ========================================================
'''
rechunk_chess
=============
Chess-scape daily weather projections are organised for each RCP and ENSEMBLE,
in files containing a single climate variable for a one month time series for 
all 1km cells in GB.
This script rechunks the chess-scape netCDF files in two ways, based
on user input:
    1 - each chunk contains a 60 year daily time series of all climatic 
        variables for 100 cells contained in each 10km2 tile of the
        British National Grid. 
    2 - each chunk contains a 60 year daily time series of all climatic 
        variables for 10000 cells contained in each 100km2 tile of the
        British National Grid. 
The climate variables of interest are: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 
'rsds', 'hurs', 'sfcWind', 'psurf' (the last only for non bias corrected projs)
More info on the variables and data in the CEDA archive:
https://catalogue.ceda.ac.uk/uuid/8194b416cbee482b89e0dfbe17c5786c
'''
from functools import partial
import multiprocessing
import os
import time
import xarray as xr
from chess.chess_manager import filter_files, osgrid2bbox, print_progress_bar
from chess.config import ChessConfig

# pylint: disable=R0914
def rechunk_chess(os_cell, rcp, ensemble, config):
    """
    Take netcdf files containing the ChessScape climate data and rechunk
    them to be in the format required for the Wofost crop yield model
    """
    nc_path = config.data_dirs['ceda_dir']
    out_path = config.data_dirs['osgb_dir']
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    # nc data parameters
    years = list(range(2020, 2081))
    climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
    # climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind', 'psurf']
    t = time.time()
    bbox = osgrid2bbox(os_cell, '10km')
    # initialise empty xr dataset
    os_chunk = xr.Dataset()

    # loop through climate_vars and files for each var (i.e. months)
    print(f'Processing cell \'{os_cell}\' ...')
    for var in climate_vars:
        counter = 1
        file_list = filter_files(rcp, years, var, ensemble, nc_path)
        list_length = len(file_list)
        print_progress_bar(0, list_length, prefix = f'{var}:', suffix = 'Complete', length = 50)
        for file in file_list:
            print_progress_bar(counter,
                             list_length,
                             prefix = f'{var}:',
                             suffix = 'Complete',
                             length = 50)
            counter += 1
            try:
                nc_file = xr.open_dataset(file)[var]
                if file is file_list[0]:
                    cell_data = nc_file.where((nc_file.x >= bbox['xmin']) &
                        (nc_file.x < bbox['xmax']) &
                        (nc_file.y >= bbox['ymin']) &
                        (nc_file.y < bbox['ymax']), drop=True)
                else:
                    df = nc_file.where((nc_file.x >= bbox['xmin']) &
                        (nc_file.x < bbox['xmax']) &
                        (nc_file.y >= bbox['ymin']) &
                        (nc_file.y < bbox['ymax']), drop=True)
                    cell_data = xr.concat([cell_data, df], dim='time')
            except FileNotFoundError:
                # print(f'Cannot open file \'{file}\'. Skipping...')
                continue

        # Add xr.DataArray for specified var to Dataset
        os_chunk[var] = cell_data

    # Sum longwave and shortwave downward surface radiation to total surface radiation
    os_chunk['rds'] = os_chunk['rlds'] + os_chunk['rsds']

    # Save on disk
    tot_time = time.time() - t
    print(f'OS cell \'{os_cell}\' processed in {tot_time:.2f} seconds\n')
    os_chunk.to_netcdf(out_path+f'{os_cell}_{rcp}_{ensemble}.nc')
# pylint: enable=R0914

if __name__ == "__main__":

    os_regions = [
        'SV', 'SW', 'SX', 'SY', 'SZ', 'TV',
        'SR', 'SS', 'ST', 'SU', 'TQ', 'TR',
        'SM', 'SN', 'SO', 'SP', 'TL', 'TM',
        'SH', 'SJ', 'SK', 'TF', 'TG', 'SC',
        'SD', 'SE', 'TA', 'NW', 'NX', 'NY',
        'NZ', 'OV', 'NR', 'NS', 'NT', 'NU',
        'NL', 'NM', 'NN', 'NO', 'NP', 'NF',
        'NG', 'NH', 'NJ', 'NK', 'NA', 'NB',
        'NC', 'ND', 'NE', 'HW', 'HX', 'HY',
        'HZ', 'HT', 'HU', 'HO', 'HP'
    ]

    os_grid = [code +  f'{num:02}' for code in os_regions for num in range(100)]

    with multiprocessing.Pool(processes=16) as pool:

        # Use the pool.map() function to parallelize the loop
        chess_config = ChessConfig('config.ini')
        RCP = 'rcp45'
        ENSEMBLE = '01'
        rechunk_chess_partial = partial(
            rechunk_chess,
            rcp=RCP,
            ensemble=ENSEMBLE,
            config=chess_config
        )
        results = results = pool.map(rechunk_chess_partial, os_grid)
    