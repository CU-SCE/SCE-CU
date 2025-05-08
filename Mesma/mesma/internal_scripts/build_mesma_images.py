import os                                                                                                                                      
import numpy as np 
import sys
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python/plugins')
sys.path.append('/opt/conda/envs/earth-lab/share/qgis/python')
import qgis
import boto3
from mesma.core.mesma import MesmaCore, MesmaModels                                                                                            
from mesma.interfaces.imports import import_library, import_image, import_library                                                                            
from mesma.interfaces.mesma_cli import create_parser, run_mesma
from typing import List
from collections import defaultdict
import argparse
from argparse import Namespace

temp_creds = {}

def run_mesma_for_image(image,spectral_library, parser):                                                                                                                                               
    # parser = create_parser()                                                                                                                       
    # args = parser.parse_args() 
    args = Namespace(
        image=image,
        library=spectral_library,
        class_name='Type',
        complexity_level=[2, 3],
        reflectance_scale_image=np.nanmax(import_image(image)),
        reflectance_scale_library=np.nanmax(np.array([
            np.array(x.values()['y'])[np.where(x.bbl())[0]]
            for x in import_library(spectral_library).profiles()
        ]).T),
        fusion_threshold=0.007,
        unconstrained=False,
        min_fraction=-0.05,
        max_fraction=1.05,
        min_shade_fraction=0.0,
        max_shade_fraction=0.8,
        max_rmse=0.025,
        residual_constraint=False,
        residual_constraint_values=(0.025, 7),
        shade=None,
        reflectance_scale_shade=None,
        output=None,
        residuals_image=False,
        spectral_weighing=False,
        band_selection=False,
        band_selection_values=(0.99, 0.01),
        cores=1
    )
    # args.image = image
    # args.library = spectral_library                                                                                                                    
    image = import_image(image)   
    spectral_library = import_library(spectral_library) 
    library = np.array([np.array(x.values()['y'])[np.where(x.bbl())[0]] for x in spectral_library.profiles()]).T

    args.reflectance_scale_image =   np.nanmax(image)  
    args.reflectance_scale_library= np.nanmax(library)

    print(args)                                                                                                                                   
    run_mesma(args) 

def download_tif_image(bucket_name,folder_name, file_names, download_path, temp_creds):
    # Create an S3 client using temporary credentials
    s3 = boto3.client(
        's3',
        aws_access_key_id=temp_creds['aws_access_key_id'],
        aws_secret_access_key=temp_creds['aws_secret_access_key'],
        aws_session_token=temp_creds['aws_session_token']
    )
    print(file_names)
    for file_name in file_names:
        try:
            local_file_name = os.path.join(download_path, file_name.split('/')[-1])
            print(f"Downloading {file_name} to {local_file_name}...")
            s3.download_file(bucket_name, os.path.join(folder_name, file_name), local_file_name)
            print(f"Downloaded {local_file_name}")
        except Exception as e:
            print(f"Error downloading {file_name}: {e}")

def upload_files_to_s3(files, bucket_name, folder_name,temp_creds, region = 'us-west-2'):
    # Create a session with temporary credentials
    session = boto3.Session(
        aws_access_key_id=temp_creds["aws_access_key_id"],
        aws_secret_access_key=temp_creds["aws_secret_access_key"],
        aws_session_token=temp_creds["aws_session_token"],
        region_name=region
    )

    # Create an S3 client using the session
    s3 = session.client('s3')

    def folder_exists(bucket, folder):
        try:
            result = s3.list_objects_v2(Bucket=bucket, Prefix=folder)
            return 'Contents' in result
        except Exception as e:
            print(f"Error checking folder existence: {e}")
            return False

    # Create folder if it does not exist
    if not folder_exists(bucket_name, folder_name):
        try:
            s3.put_object(Bucket=bucket_name, Key=(folder_name + '/'))
            print(f"Folder '{folder_name}' created in bucket '{bucket_name}'.")
        except Exception as e:
            print(f"Error creating folder: {e}")
            return

    # Upload each file to the specified folder
    for file in files:
        try:
            file_name = os.path.basename(file)
            s3.upload_file(file, bucket_name, f"{folder_name}/{file_name}")
            print(f"File '{file_name}' uploaded to '{folder_name}' in bucket '{bucket_name}'.")
        except Exception as e:
            print(f"Error uploading file '{file}': {e}")


def get_files_with_substring(folder_path, substring):
    files = os.listdir(folder_path)
    matching_files = [f for f in files if f.startswith(substring)]
    full_paths = [os.path.join(folder_path, f) for f in matching_files]
    return full_paths

def select_files_except_tif(folder_path):
    selected_files = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            selected_files.append(file_path)
    
    return selected_files


def group_files_by_prefix(files, prefix_length):
    grouped_files = defaultdict(list)
    
    for file_name in files:
        file_path = file_name
        if os.path.isfile(file_path):
            prefix = file_name.split("/")[-1][:prefix_length]
            grouped_files[prefix].append(file_path)
    
    return grouped_files


def upload_files(image_folder,image_files,s3_bucket):
    file_paths = select_files_except_tif(image_folder)

    grouped_files = group_files_by_prefix(file_paths, 18)

    for key in grouped_files.keys():
        s3_folder_name = "_".join(key.split("_")[0:6])
        s3_folder_name = "mesma/" + s3_folder_name
        print(grouped_files[key], s3_folder_name)
        print()
        upload_files_to_s3(grouped_files[key], s3_bucket, s3_folder_name, temp_creds)

    

def build(s3_bucket:str = None, s3_output_folder:str = None, image_files: List[str] = None,parser:argparse.ArgumentParser = None):
    image_folder = "/tmp/images"
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"Folder '{image_folder}' created.")


    download_tif_image(s3_bucket, s3_output_folder, image_files, image_folder, temp_creds)
    for image in image_files:
        image_path = "/tmp/images/"+image
        spectral_library = "/workspace/library/38_output.sli"
        run_mesma_for_image(image_path,spectral_library, parser)

    upload_files(image_folder,image_files,s3_bucket)
