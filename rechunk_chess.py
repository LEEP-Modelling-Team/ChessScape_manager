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
    1 - each chunk contains a the time series of all climatic 
        variables for 100 cells contained in each 10km2 tile of the
        British National Grid. 
    2 - each chunk contains the daily time series of all climatic 
        variables for 10000 cells contained in each 100km2 tile of the
        British National Grid. 
The climate variables of interest are: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 
'rsds', 'hurs', 'sfcWind', 'psurf' (the last only for non bias corrected projs)
More info on the variables and data in the CEDA archive:
https://catalogue.ceda.ac.uk/uuid/8194b416cbee482b89e0dfbe17c5786c
'''
from functools import partial
import argparse
import multiprocessing
import os
import time
import xarray as xr
from chess.chess_manager import filter_files, osgrid2bbox, print_progress_bar
from chess.config import ChessConfig


def _format_duration(seconds):
    """Format seconds as HH:MM:SS for lightweight progress reporting."""
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{hours:02}:{minutes:02}:{secs:02}'

# pylint: disable=R0914
def rechunk_chess(
        os_cell,
        rcp,
        ensemble,
        config,
        file_map=None,
        skip_existing=True,
        verbose=False
    ):
    """
    Take netcdf files containing the ChessScape climate data and rechunk
    them to be in the format required for the Wofost crop yield model
    """
    try:
        nc_path = config.data_dirs['ceda_dir']
        out_path = config.data_dirs['osgb_dir']
        os.makedirs(out_path, exist_ok=True)
        out_file = os.path.join(out_path, f'{os_cell}_{rcp}_{ensemble}.nc')

        # Resume-friendly: skip tiles that were already processed.
        if skip_existing and os.path.exists(out_file):
            return os_cell, True, 'skipped_existing'

        # nc data parameters
        years = list(range(1980, 2081))
        climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
        # climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind', 'psurf']
        t = time.time()
        bbox = osgrid2bbox(os_cell, '10km')
        # initialise empty xr dataset
        os_chunk = xr.Dataset()

        # loop through climate_vars and files for each var (i.e. months)
        if verbose:
            print(f'Processing cell \'{os_cell}\' ...')
        for var in climate_vars:
            file_list = None
            if file_map is not None:
                file_list = file_map.get(var, [])
            if file_list is None:
                file_list = filter_files(rcp, years, var, ensemble, nc_path)

            list_length = len(file_list)
            if verbose and list_length > 0:
                print_progress_bar(0, list_length, prefix=f'{os_cell} {var}:', suffix='Complete', length=50)

            cell_data_parts = []
            counter = 1
            for file in file_list:
                if verbose and list_length > 0:
                    print_progress_bar(counter,
                                     list_length,
                                     prefix=f'{os_cell} {var}:',
                                     suffix='Complete',
                                     length=50)
                counter += 1
                try:
                    with xr.open_dataset(file, engine='netcdf4') as ds:
                        nc_file = ds[var]
                        # Use .sel() with slice for more reliable spatial subsetting
                        filtered = nc_file.sel(
                            x=slice(bbox['xmin'], bbox['xmax']),
                            y=slice(bbox['ymin'], bbox['ymax'])
                        )

                        # Skip if no data points match the bounding box
                        if filtered.size == 0:
                            continue

                        # Load immediately so data remain valid after context manager closes file.
                        cell_data_parts.append(filtered.load())
                except (FileNotFoundError, OSError, ValueError) as e:
                    if verbose:
                        print(f'[{os_cell}] Error with file \'{file}\': {e}. Skipping...')
                    continue

            # Add xr.DataArray for specified var to Dataset
            if cell_data_parts:
                os_chunk[var] = xr.concat(cell_data_parts, dim='time')

        # Sum longwave and shortwave downward surface radiation to total surface radiation
        if 'rlds' in os_chunk and 'rsds' in os_chunk:
            os_chunk['rds'] = os_chunk['rlds'] + os_chunk['rsds']

        if not os_chunk.data_vars:
            return os_cell, False, 'no_data_for_tile'

        # Save on disk
        tot_time = time.time() - t
        if verbose:
            print(f'OS cell \'{os_cell}\' processed in {tot_time:.2f} seconds\n')
        os_chunk.to_netcdf(out_file)
        return os_cell, True, None
    except Exception as e:
        print(f'[{os_cell}] FAILED: {type(e).__name__}: {e}')
        return os_cell, False, str(e)
# pylint: enable=R0914


# pylint: disable=R0914
def rechunk_region_100km(
        region,
        rcp,
        ensemble,
        config,
        file_map,
        skip_existing=True,
        verbose=False
    ):
    """
    Rechunk by 100km region so each source file is opened once per region and
    split into the 100 10km tiles in memory.
    """
    try:
        out_path = config.data_dirs['osgb_dir']
        os.makedirs(out_path, exist_ok=True)

        climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
        tile_ids = [f'{region}{num:02}' for num in range(100)]

        if skip_existing:
            target_tiles = [
                tile for tile in tile_ids
                if not os.path.exists(os.path.join(out_path, f'{tile}_{rcp}_{ensemble}.nc'))
            ]
        else:
            target_tiles = tile_ids
            # Full rerun mode: remove existing outputs first.
            for tile in tile_ids:
                out_file = os.path.join(out_path, f'{tile}_{rcp}_{ensemble}.nc')
                if os.path.exists(out_file):
                    os.remove(out_file)

        if not target_tiles:
            return region, True, {'processed': 0, 'skipped_existing': len(tile_ids), 'failed': []}

        t = time.time()
        region_bbox = osgrid2bbox(region, '100km')
        tile_bboxes = {tile: osgrid2bbox(tile, '10km') for tile in target_tiles}
        file_written = {tile: False for tile in target_tiles}
        failed_tiles = []

        if verbose:
            print(f'Processing 100km region \"{region}\" with {len(target_tiles)} target tiles...')

        for var in climate_vars:
            file_list = file_map.get(var, [])
            list_length = len(file_list)
            if verbose and list_length > 0:
                print_progress_bar(0, list_length, prefix=f'{region} {var}:', suffix='Complete', length=50)

            tile_parts = {tile: [] for tile in target_tiles}
            counter = 1
            for file in file_list:
                if verbose and list_length > 0:
                    print_progress_bar(counter,
                                     list_length,
                                     prefix=f'{region} {var}:',
                                     suffix='Complete',
                                     length=50)
                counter += 1
                try:
                    with xr.open_dataset(file, engine='netcdf4') as ds:
                        region_data = ds[var].sel(
                            x=slice(region_bbox['xmin'], region_bbox['xmax']),
                            y=slice(region_bbox['ymin'], region_bbox['ymax'])
                        )
                        if region_data.size == 0:
                            continue

                        for tile, bbox in tile_bboxes.items():
                            tile_data = region_data.sel(
                                x=slice(bbox['xmin'], bbox['xmax']),
                                y=slice(bbox['ymin'], bbox['ymax'])
                            )
                            if tile_data.size == 0:
                                continue
                            tile_parts[tile].append(tile_data.load())
                except (FileNotFoundError, OSError, ValueError) as exc:
                    if verbose:
                        print(f'[{region}] Error with file \"{file}\": {exc}. Skipping...')
                    continue

            # Persist this variable for each tile and free memory before next variable.
            for tile in target_tiles:
                parts = tile_parts[tile]
                if not parts:
                    continue
                out_file = os.path.join(out_path, f'{tile}_{rcp}_{ensemble}.nc')
                tile_var = xr.concat(parts, dim='time').rename(var)
                mode = 'a' if file_written[tile] else 'w'
                tile_var.to_netcdf(out_file, mode=mode)
                file_written[tile] = True

        # Add derived rds once all base variables are persisted.
        for tile in target_tiles:
            if not file_written[tile]:
                failed_tiles.append((tile, 'no_data_for_tile'))
                continue

            out_file = os.path.join(out_path, f'{tile}_{rcp}_{ensemble}.nc')
            try:
                with xr.open_dataset(out_file) as ds_tile:
                    if 'rlds' in ds_tile and 'rsds' in ds_tile and 'rds' not in ds_tile:
                        rds_data = (ds_tile['rlds'] + ds_tile['rsds']).rename('rds').load()
                    else:
                        rds_data = None
                if rds_data is not None:
                    rds_data.to_netcdf(out_file, mode='a')
            except (FileNotFoundError, OSError, ValueError) as exc:
                failed_tiles.append((tile, str(exc)))

        elapsed = time.time() - t
        if verbose:
            print(f'Region \"{region}\" completed in {elapsed:.2f}s')

        return region, True, {
            'processed': sum(1 for tile in target_tiles if file_written[tile]),
            'skipped_existing': len(tile_ids) - len(target_tiles),
            'failed': failed_tiles,
            'elapsed_seconds': elapsed
        }
    except Exception as exc:
        print(f'[{region}] FAILED: {type(exc).__name__}: {exc}')
        return region, False, {
            'processed': 0,
            'skipped_existing': 0,
            'failed': [(region, str(exc))],
            'elapsed_seconds': 0.0
        }
# pylint: enable=R0914

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Rechunk CHESS-SCAPE files by 100km region into 10km tile outputs.'
    )
    parser.add_argument('--rcp', default='rcp45', help='RCP scenario to process (default: rcp45).')
    parser.add_argument('--ensemble', default='01', help='Ensemble member to process (default: 01).')
    parser.add_argument('--workers', type=int, default=18, help='Number of parallel workers (default: 18).')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed progress logging.')
    parser.add_argument(
        '--progress-every',
        type=int,
        default=1,
        help='Print a global progress update every N completed regions (default: 1).'
    )
    parser.add_argument(
        '--progress-file',
        default='',
        help='Optional path for writing machine-readable progress updates.'
    )
    skip_group = parser.add_mutually_exclusive_group()
    skip_group.add_argument(
        '--skip-existing',
        dest='skip_existing',
        action='store_true',
        help='Skip tile outputs that already exist (resume mode).'
    )
    skip_group.add_argument(
        '--overwrite-existing',
        dest='skip_existing',
        action='store_false',
        help='Overwrite any existing tile outputs (full rerun mode).'
    )
    parser.set_defaults(skip_existing=True)
    args = parser.parse_args()

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

    # Use the pool.map() function to parallelize the loop
    chess_config = ChessConfig('config.ini')
    RCP = args.rcp
    ENSEMBLE = args.ensemble
    YEARS = list(range(1980, 2081))
    CLIMATE_VARS = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']

    # Precompute file lists once instead of re-scanning the directory in every worker.
    nc_path = chess_config.data_dirs['ceda_dir']
    file_map = {
        var: filter_files(RCP, YEARS, var, ENSEMBLE, nc_path)
        for var in CLIMATE_VARS
    }

    with multiprocessing.Pool(processes=args.workers) as pool:
        rechunk_chess_partial = partial(
            rechunk_region_100km,
            rcp=RCP,
            ensemble=ENSEMBLE,
            config=chess_config,
            file_map=file_map,
            skip_existing=args.skip_existing,
            verbose=args.verbose
        )
        total_regions = len(os_regions)
        completed_regions = 0
        start_time = time.time()
        results = []

        if args.progress_every < 1:
            args.progress_every = 1

        for result in pool.imap_unordered(rechunk_chess_partial, os_regions):
            results.append(result)
            completed_regions += 1

            if completed_regions % args.progress_every == 0 or completed_regions == total_regions:
                elapsed = time.time() - start_time
                region_rate = completed_regions / elapsed if elapsed > 0 else 0
                remaining = total_regions - completed_regions
                eta_seconds = int(remaining / region_rate) if region_rate > 0 else 0
                pct = (completed_regions / total_regions) * 100

                progress_line = (
                    f'Progress: {completed_regions}/{total_regions} regions '
                    f'({pct:.1f}%) | elapsed {_format_duration(elapsed)} '
                    f'| eta {_format_duration(eta_seconds)} '
                    f'| rate {region_rate:.2f} regions/s'
                )
                print(progress_line)

                if args.progress_file:
                    with open(args.progress_file, 'w', encoding='utf-8') as pfile:
                        pfile.write(
                            '{\n'
                            f'  "completed_regions": {completed_regions},\n'
                            f'  "total_regions": {total_regions},\n'
                            f'  "percent_complete": {pct:.3f},\n'
                            f'  "elapsed_seconds": {elapsed:.3f},\n'
                            f'  "eta_seconds": {eta_seconds},\n'
                            f'  "regions_per_second": {region_rate:.6f}\n'
                            '}\n'
                        )
    
    # Print summary
    total_processed = 0
    total_skipped = 0
    failed_tiles = []
    failed_regions = []

    for region, success, stats in results:
        if not success:
            failed_regions.append((region, stats))
            continue
        total_processed += stats.get('processed', 0)
        total_skipped += stats.get('skipped_existing', 0)
        failed_tiles.extend(stats.get('failed', []))

    print(f'\n=== Processing summary ===')
    print(f'Processed tiles: {total_processed}')
    print(f'Skipped existing tiles: {total_skipped}')
    if failed_tiles:
        print(f'Failed tiles: {len(failed_tiles)}')
        for tile, err in failed_tiles:
            print(f'  {tile}: {err}')
    if failed_regions:
        print(f'Failed regions: {len(failed_regions)}')
        for region, err in failed_regions:
            print(f'  {region}: {err}')
    