# The following codes to import, clean, and process Sentinel-2 data using VSI and AWS were written by Lilly Jones and Erick Verleye; edited by Ty Tuff, pseudocode by Cibele Amaral. 

#imports

import os
import logging
import multiprocessing as mp
from argparse import Namespace
from datetime import datetime, timedelta
from typing import List, Tuple
import boto3
import geojson
import tqdm
from shapely.geometry import Polygon


def get_aws_creds():
    return {}


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3',**get_aws_creds())
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        logging.error(e)
        return False
    return True

# Original AWS code by Erick Verleye, ESIIL Software Developer 2023-08-08, lightly edited by Lilly Jones for SCE project
# Code downloads Sentinel Level-1 C data from S3 with Python for a given latitude, longitude, and date range.
# An AWS account is needed and will be charged (a small amount) for any data downloaded.

# Use boto3 to create a connection to the AWS account. Initialization of the boto3.session object changes depending on the environment you are running this code in:

# Using the AWS CLI from a personal computer to log in, the profile name will typically be default.
# Using a federated access login, the profile name will typically be the name of the software.
# Using S3 configured IAM profile, no profile name is required.
# Each of these arguments, if applicable, can be found in the aws credentials file typically found at ~/.aws/credentials

# session = boto3.Session(profile_name='saml')

session = boto3.Session()

# Define constants
SENTINEL_2_BUCKET_NAME = 'sentinel-s2-l1c'  # Name of the s3 bucket on AWS hosting the sentinel-2 data


# find_overlapping_mgrs Sentinel-2 data is organized depending on which Military Grid Reference System (MGRS) square that it belongs to. This function converts a bounding box defined in    # lat/lon as [min_lon, min_lat, max_lon, max_lat] to the military grid squares that is overlaps. More information on # # the MGRS can be found at                                                       # https://www.maptools.com/tutorials/mgrs/quick_guide. NOTE: You will have to download the mgrs_lookup.geojson file from # # # # # https://github.com/CU-ESIIL/data-                        # library/blob/main/docs/remote_sensing/sentinel2_aws/mgrs_lookup.geojson and place it into the working directory that # # this code is being run from.

def find_overlapping_mgrs(bounds: List[float]) -> List[str]:
    """
    Files in the Sinergise Sentinel2 S3 bucket are organized by which military grid they overlap. Thus, the
    military grids that overlap the input bounding box defined in lat / lon must be found. A lookup table that
    includes each grid name and its geometry is used to find the overlapping grids.
    Args:
        bounds (list): Bounding box definition as [min_lon, min_lat, max_lon, max_lat]
    """
    print('Finding overlapping tiles... ')
    input_bounds = Polygon([(bounds[0], bounds[1]), (bounds[2], bounds[1]), (bounds[2], bounds[3]),
                            (bounds[0], bounds[3]), (bounds[0], bounds[1])])
    with open('california-100km-mgrs.geojson', 'r') as f:
        ft = geojson.load(f)
        return [i['properties']['GRID1MIL'] + i['properties']['GRID100K'] for i in ft[1:] if
                input_bounds.intersects(Polygon(i['geometry']['coordinates'][0]))]

# find_available_files finds the set of available files in the s3 bucket given a date range, lat/lon bounds, and list of bands.

def find_available_files(s3_client, bounds: List[float], start_date: datetime, end_date: datetime,
                         bands: List[str],mgrs_grids) -> List[Tuple[str, str]]:
    """
    Given a bounding box and start / end date, finds which files are available on the bucket and
    meet the search criteria
    Args:
        bounds (list): Lower left and top right corner of bounding box defined in
        lat / lon [min_lon, min_lat, max_lon, max_lat]
        start_date (str): Beginning of requested data creation date YYYY-MM-DD
        end_date (str): End of requested data creation date YYYY-MM-DD
    """
    date_paths = []
    ref_date = start_date
    while ref_date <= end_date:
        tt = ref_date.timetuple()
        date_paths.append(f'/{tt.tm_year}/{tt.tm_mon}/{tt.tm_mday}/')
        ref_date = ref_date + timedelta(days=1)

    info = []
    # mgrs_grids = find_overlapping_mgrs(bounds)
    # mgrs_grids = ["11SKU", "11SMT","11SLU","11SLV","11SNT"]
    # mgrs_grids = ["11SKV", "11SKA", "11SLA", "11SKB","10SGF","10SGG","10SFG","10SFH","10SGH"]

    print(mgrs_grids)
    i=0
    for grid_string in mgrs_grids:
        i+=1
        utm_code = grid_string[:2]
        print(grid_string)
        latitude_band = grid_string[2]
        square = grid_string[3:5]
        grid = f'tiles/{utm_code}/{latitude_band}/{square}'
        response = s3_client.list_objects_v2(
            Bucket=SENTINEL_2_BUCKET_NAME,
            Prefix=grid + '/',
            MaxKeys=300,
            RequestPayer='requester'
        )
        if 'Contents' not in list(response.keys()):
            continue

        for date in date_paths:
            response = s3_client.list_objects_v2(
                Bucket=SENTINEL_2_BUCKET_NAME,
                Prefix=grid + date + '0/',  # '0/' is for the sequence, which in most cases will be 0
                MaxKeys=100,
                RequestPayer='requester'
            )
            if 'Contents' in list(response.keys()):
#                 print([v['Key'] for v in response['Contents']])
                info += [
                    (v['Key'], v['Size']) for v in response['Contents'] 
                ]

    return info



# This function is designed to download the files in parallel, so a download_task function is defined as well. 
# Note that multiprocessing will not work as implemented here in iPython (Jupyter # # notebooks, etc.) and so that block of code is commented out. 
# If you are running this in a different environment and would like to download in parallel, un-comment this block and comment the sequential block below.


def download_task(namespace: Namespace) -> None:
    """
    Downloads a single file from the indicated s3 bucket. This function is intended to be spawned in parallel from the
    parent process.
    Args:
        namespace (Namespace): Contains the bucket name, s3 file name, and destination required for s3 download request.
        Each value in the namespace must be a pickle-izable type (i.e. str).
    """
#     session = boto3.Session(profile_name=namespace.profile_name)
    session = boto3.Session()
    s3 = session.client('s3',**get_aws_creds())
    s3.download_file(namespace.bucket_name, namespace.available_file,
                     namespace.dest,
                     ExtraArgs={'RequestPayer': 'requester'}
                     )
    file_name = namespace.dest.split("\\")[-1]
    file_downloaded_destination =file_name
    upload_file(file_downloaded_destination,namespace.s3_bucket, '{}/{}'.format(namespace.s3_folder,file_name))
    os.remove(file_downloaded_destination)


def download(session, bounds: List[float], start_date: datetime, end_date: datetime,mgrs_grids,
             bands: List[float], buffer: float = None, s3_bucket:str = None, s3_folder:str = None) -> None:
    """
    Downloads a list of .jp2 files from the Sinergise Sentinel2 LC1 bucket given a bounding box defined in lat/long, a buffer in meters, and a start and end date. Only Bands 2-4 are requested.
     Args:
         bounds (list): Bounding box defined in lat / lon [min_lon, min_lat, max_lon, max_lat]
         buffer (float): Amount by which to extend the bounding box by, in meters
         start_date (str): Beginning of requested data creation date YYYY-MM-DD
         end_date (str): End of requested data creation date YYYY-MM-DD
         bands (list): The bands to download for each file. Ex. ['B02', 'B03', 'B04', 'B08'] for R, G, B, and
         near wave IR, respectively
         out_dir (str): Path to directory where downloaded files will be written to
    """
    # Convert the buffer from meters to degrees lat/long at the equator
    if buffer is not None:
        buffer /= 111000

        # Adjust the bounding box to include the buffer (subtract from min lat/long values, add to max lat/long values)
        bounds[0] -= buffer
        bounds[1] -= buffer
        bounds[2] += buffer
        bounds[3] += buffer
        
    s3_client = session.client('s3',**get_aws_creds())
    available_files = find_available_files(s3_client, bounds, start_date, end_date, bands,mgrs_grids)
    
    
    total_data = 0
    args = []
    contents = s3_client.list_objects_v2(Bucket = s3_bucket,Prefix=s3_folder)["Contents"]
    s3_files = [content['Key'].split("/")[1].replace("_", "/").replace("MSK/CLOUDS/","MSK_CLOUDS_") for content in contents] 
    for file_info in available_files:
        if(file_info[0].split("tiles/")[1] not in s3_files):
            file_path = file_info[0]
            if '/preview/' in file_path:
                continue
            new_file_path = file_path.replace('_qi_', '').replace('/', '_').replace('tiles_', '')
            created_file_path = os.path.join("/tmp", new_file_path)

            if os.path.exists(created_file_path):
                continue

            total_data += file_info[1]

            args.append(Namespace(available_file=file_path, bucket_name=SENTINEL_2_BUCKET_NAME, profile_name=session.profile_name,
                                  dest=created_file_path, s3_bucket=s3_bucket, s3_folder=s3_folder))

    total_data /= 1E9
    print(f'Found {len(args)} files for download. Total size of files is'
          f' {round(total_data, 2)}GB and estimated cost will be ${round(0.09 * total_data, 2)}'
          )
    
    # For multiprocessing when being run in iPython (Jupyter notebook, etc.)
    with mp.Pool(mp.cpu_count() - 1) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(download_task, args), total=len(args)):
            pass