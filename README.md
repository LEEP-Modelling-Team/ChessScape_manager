# ChessScape Manager

The ChessScape Manager allows to download and process the Chess-Scape climate projections at 1km resolution produced by the UK Centre for Ecology and Hydrology from the Met-Office UKCP18 Climate Projections.

## FEATURES
Two main features are contained in this repository:
1. Automatic bulk download of the data via HTTP from CEDA: bulk_downloader.py  
2. Re-organise the data: rechunk_chess.py

## USE
**1 - BULK DOWNLOADER: bulk_downloader.py**  
    This script downloads Chess-Scape data from CEDA using HTTP with Bearer token authentication based on rcp, climate variable and ensemble member of interest.
    Unless a user specifies a custom selection of data to download, this script will download automatically all available years (1980-2080), for all 4 ensemble members for all available RCPs and for the following climate variables: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind'. More variables can be downloaded if available.    
    For information on the available RCPs, ensemble members and climate variables visit CEDA at https://tinyurl.com/muezkh5b

**2 - DATA REORGANISATION: rechunk_chess.py**  
    Chess-scape daily weather projections are organised for each RCP and ensemble member in files containing a single climate variable for a one month time series for 
    all 1km cells in GB. The script now uses a 100km-first processing strategy for better performance: each source monthly netCDF file is read once per 100km region and then split into the 100 corresponding 10km tiles in memory.
    The output remains one netCDF per 10km tile, containing a daily time series of all climatic variables for the 100 cells in that tile.
    This greatly reduces repeated file I/O compared with tile-by-tile reading and is designed for faster large-scale rechunking.

## SETUP
Before using the ChessScape Manager, make sure to register for a CEDA account and obtain access to the CHESS-SCAPE dataset (https://help.ceda.ac.uk/article/5100-archive-access-tokens).  
After having obtained CEDA credentials:  

1. Clone the repository to your local machine

2. Create the conda environment and install dependencies:  
    ```
    conda env create -f environment.yml
    conda activate chess_manager
    ```  

3. Open the 'config.ini' file with a text editor and edit the paths where you want the data to be stored:  
    'ceda_dir' will contain the raw netcdf files downloaded from CEDA  
    'osgb_dir' will contain the new files rechunked to be associated to British National Grid tiles (see Section 2 in USE above)  
    ```
    ceda_dir = Path\to\Raw\Data\
    osgb_dir = Path\to\Rechunked\Data\
    ```
4. Add the following environment variables:   
    ```    
    'CEDA_user': your CEDA Username
    'CEDA_pwd': your CEDA Password
    ```
**N.B.**  
Do not hard code your user credentials in the config.ini file!

**Note:** The download script uses CEDA's HTTP Bearer token authentication. Tokens are automatically generated and cached in `~/.cedatoken` for reuse until expiry (3 days).

## HOW TO RUN
Open a terminal and navigate to the main folder containing the repository.
- To run the bulk downloader, type in terminal  
    `python bulk_downloader.py`
- To run the file rechunking programme, after having downloaded the dataset, type in terminal:  
        `python rechunk_chess.py`  

### Rechunking arguments
The rechunking script supports the following command-line arguments:

- `--rcp` RCP scenario to process (default: `rcp45`)
- `--ensemble` Ensemble member to process (default: `01`)
- `--start-year` First year to include (default: `1980`)
- `--end-year` Last year to include (default: `2080`)
- `--workers` Number of parallel workers (default: `18`)
- `--verbose` Enable detailed progress logging
- `--progress-every` Print one lightweight global progress update every N completed regions (default: `1`)
- `--progress-file` Optional path to write machine-readable progress status (JSON-like text)
- `--validate-time` Run a preflight check that reports per-variable time coverage before processing
- `--regions` Optional comma-separated list of 100km region codes to process (for quick tests)
- `--skip-existing` Skip tile outputs already present on disk (resume mode, default)
- `--overwrite-existing` Remove and regenerate existing tile outputs (full rerun mode)

Examples:

- Resume an interrupted run and skip existing outputs:
    `python rechunk_chess.py --skip-existing --workers 8`
- Force full rerun of all outputs:
    `python rechunk_chess.py --overwrite-existing --workers 8`
- Show less frequent progress updates (every 5 completed regions):
    `python rechunk_chess.py --skip-existing --workers 8 --progress-every 5`
- Write progress to a status file while running:
    `python rechunk_chess.py --skip-existing --workers 8 --progress-file rechunk_progress.json`
- Validate variable time coverage before a long run:
    `python rechunk_chess.py --skip-existing --workers 8 --validate-time`
- Process only years 2020 to 2080:
    `python rechunk_chess.py --skip-existing --workers 8 --start-year 2020 --end-year 2080`
- Test the pipeline on a small subset of regions before full run:
    `python rechunk_chess.py --overwrite-existing --workers 4 --regions SV,SW --start-year 2020 --end-year 2022`

Both scripts can take user-defined input parameters (see docstrings in both scripts for further options and instructions).
