import re
import os
import numpy as np
from osgeo import gdal
import rasterio
from collections import defaultdict
import logging
import boto3
import botocore


SCE_folder = "/workspace/"


# update the temporary credentials
def get_aws_creds():
 return {}



def upload_file(file_name, bucket, object_name=None):
    print("Upload", file_name, "to s3 bucket" )
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


def delete_files(files):
  print(files)
  for file in files:
    if(os.path.isfile(file)):
      os.remove(file)


def download_from_s3(s3_client, bucket, file, download_dest):
  print("Downloading", file, "from s3 bucket" )
  print("Download destination", download_dest)
  s3_client.download_file(bucket, file, download_dest)


def get_s3_files(s3, bucket, prefix):
  paginator = s3.get_paginator('list_objects_v2')
  pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

  files = []
  for page in pages:
      for i in page['Contents']:
        if i['Key']!= prefix+"/":
          files.append(i['Key'].split("/")[1])
  return files


def grouping_files(files_list):
  groups = defaultdict(list)

  for file in files_list:
      key = "".join(file.split("_")[0:6])
      groups[key].append(file)

  grouped_strings = list(groups.values())

  return grouped_strings

def resample_bands(resampling_dir):
  print("Resampling Bands")
  bands_to_resample = ["B05", "B06", "B07","B11","B12"]
  files_list = os.listdir(resampling_dir)
  for file in files_list:
    band = file.split("_")[-1].split(".")[0]
    if(band in bands_to_resample and ".jp2" in file):
      file_path  = resampling_dir + file
      print("Resampling", file_path)
      print(os.path.isfile(file_path))
      ds = gdal.Open('/workspace/input_dir/11_S_LT_2024_10_2_0_B05.jp2')
      print(ds)
      gdal.Warp(file_path, file_path, xRes=10, yRes=10)

def read_jp2(image_path):
    with rasterio.open(image_path) as src:
        image = src.read(1)  # Read the first band
        profile = src.profile
    return image, profile




def apply_detfoo_mask(spectral_band, detfoo_mask):
    masked_band = np.where(detfoo_mask != 1, spectral_band, np.nan)  # Masking with NaN
    return masked_band

def mask_clouds_and_stack_bands(band_files, detfoo_files, output_file):

    band_arrays = []
    meta = None

    for idx, band_file in enumerate(band_files):
        # Open each JP2 band
        with rasterio.open(band_file, driver="JP2OpenJPEG") as src:
            # Read the band data
            band_data = src.read(1)  # Read the first (or only) band
            band_arrays.append(band_data)
            band_crs = src.crs

            # Store metadata from the first band
            if idx == 0:
                meta = src.meta.copy()

    # Update metadata for the output GeoTIFF
    meta.update({
        "driver": "GTiff",
        "count": len(band_arrays),  # Number of bands
        "dtype": band_arrays[0].dtype , # Use the same dtype as the first band
        "crs":band_crs
    })


    # Write the stacked bands to the output GeoTIFF
    with rasterio.open(output_file, "w", **meta) as dst:
        for i, band_array in enumerate(band_arrays, start=1):
            dst.write(band_array, indexes=i)

    print(f"Stacked GeoTIFF written to {output_file}")



def process_images(s3_bucket:str, s3_input_folder:str, s3_output_folder:str):
  s3_bucket = s3_bucket  # Update the AWS bucket
  s3_input_folder = s3_input_folder # update the AWS bucket input folder containing the downloaded the sentinel images
  s3_output_folder = s3_output_folder # update the AWS bucket folder containing the downloaded the sentinel images
  drive_input_dir = SCE_folder + "input_dir/"
  drive_output_dir = SCE_folder + "output_dir/"
  session = boto3.Session()
  client_config = botocore.config.Config(max_pool_connections=50)
  s3_client = session.client('s3',**get_aws_creds(), config=client_config)
  try:
    s3_output_contents = s3_client.list_objects_v2(Bucket = s3_bucket,Prefix=s3_output_folder)["Contents"]
    s3_output_files = [content['Key'].split("/")[1].replace(" ", "") for content in s3_output_contents]
  except:
    s3_output_files = []

  image_file_names = get_s3_files(s3_client, s3_bucket, s3_input_folder)

  group_files = grouping_files(image_file_names)

  error_files = []

  print("Number of Files to be processed:",len(group_files))

  def preprocess_images(files):
    band_file_regex_pattern= r"^\d{2}_[A-Za-z]_[A-Za-z]{2}_\d{4}_\d{1,2}_\d{1,2}_\d{1,2}_B(?!01|09|10)\d{1,2}\.jp2$"
    band_files = [item for item in files if re.match(band_file_regex_pattern, item)]
    detfoo_files = [i for i in files if "DETFOO" in i]
    output_file = "_".join(band_files[0].split("_")[0:6]) + ".tif"
    if(output_file in s3_output_files or output_file in error_files or len(band_files)!=9):
      return

    band_files_path = [drive_input_dir + i for i in band_files]
    deftoo_files_path = [drive_input_dir + i for i in detfoo_files]
    full_output_file = ""

    # try:
    for index in range(len(band_files)):
        download_from_s3(s3_client, s3_bucket, s3_input_folder+"/"+band_files[index], band_files_path[index])

    output_file = "_".join(band_files[0].split("_")[0:6]) + ".tif"

    print("Processing: ", output_file)

    full_output_file = drive_output_dir + output_file


    resample_bands(drive_input_dir)
    mask_clouds_and_stack_bands(band_files_path, deftoo_files_path, full_output_file)
    upload_file(full_output_file,s3_bucket, s3_output_folder+'/ {}'.format(output_file))

    # except Exception as e:
    #   print(e)
    #   error_files.append(output_file)
    #   print(error_files)

    files_to_be_deleted = band_files_path + deftoo_files_path
    files_to_be_deleted = band_files_path + deftoo_files_path
    files_to_be_deleted.append(full_output_file)
    delete_files(files_to_be_deleted)

  count = 1
  for files in reversed(group_files):
    if (len(files)==0 or files[0]==""):
      continue
    preprocess_images(files)
    print(count,":",files)
    count+=1