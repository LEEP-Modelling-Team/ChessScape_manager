# ChessScape Manager

The ChessScape Manager allows to download and process the Chess-Scape climate projections at 1km resolution produced by the UK Centre for Ecology and Hydrology from the Met-Office UKCP18 Climate Projections.

## FEATURES
Two main features are contained in this repository:
1. Automatic bulk download of the data through FTP from CEDA: bulk_downloader.py  
2. Re-organise the data: rechunk_chess.py

## USE
**1 - BULK DOWNLOADER: bulk_downloader.py**  
    This script allows to connect to the CEDA FTP server and download the Chess-Scape data based on rcp, climate variable and ensemble member of interest.
    Unless a user specifies a custom selection the data to download, this script will download automatically all available years (1980-2080), for all 4 ensemble members for all available RCPs and for the following climate variables: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind'. More variables can be downloaded if available.    
    For information on the available RCPs, ensemble members and climate variables visit CEDA at https://tinyurl.com/muezkh5b

**2 - DATA REORGANISATION: rechunk_chess.py**  
    Chess-scape daily weather projections are organised for each RCP and ensemble member in files containing a single climate variable for a one month time series for 
    all 1km cells in GB. This script rechunks the chess-scape netCDF files in two ways, based on user input:
    1 - each chunk contains a daily time series of all climatic variables for 100 cells contained in each 10km2 tile of the British National Grid.
    2 - each chunk contains a daily time series of all climatic variables for 10000 cells contained in each 100km2 tile of the British National Grid.  
    For both cases, the length of the time series will be based on the years avaiable, which depend on whether the user has downloaded all available years or a custom range (see bulkdownloader.py above)

## SETUP
Before using the ChessScape Manager, make sure to obtain access authorisation from CEDA (https://help.ceda.ac.uk/article/280-ftp).  
After having obtained the credentials from CEDA to connect to their FTP server:  

1. Clone the repository to your local machine

2. Install all the required dependencies running the following command:  
    ```
    pip install -r requirements.txt
    ```  

3. Open the 'config.ini' file with a text editor and edit the paths where you want the data to be stored:  
    'ceda_dir' will contain the raw netcdf files downloaded from CEDA  
    'osgb_dir' will contain the new files rechunked to be associated to British National Grid tiles (see Section 2 in USE above)  
    ```
    ceda_dir = Path\to\Raw\Data\
    osgb_dir = Path\to\Rechuncked\Data\
    ```
4. Add the following environment variables:   
    ```    
    'CEDA_user': your CEDA FTP Username
    'CEDA_pwd': your CEDA FTP Pssword
    ```
**N.B.**  
Do not hard code your user credentials in the config.ini file!

## HOW TO RUN
Open a terminal and navigate to the main folder containing the repository.
- To run the bulk downloader, type in terminal  
    `python bulk_downloader.py`
- To run the file rechunking programme, after having downloaded the dataset, type in terminal:  
    `python rechunk_chess.py`  
    
Both commands will run the programmes with default parameters. Both scripts can take user-defined input parameters (see docstring in both scripts for the available options and further instructions)
