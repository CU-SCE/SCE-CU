import sys
from image_processing import process_images
import boto3
from datetime import datetime
import argparse
import os




if __name__ == "__main__":


    session = boto3.Session()

    parser = argparse.ArgumentParser(description="MESMA Pipeline Entrypoint")

    parser.add_argument("--s3_bucket", type=str, help="eg: sce.sentinel2")
    parser.add_argument("--s3_input_folder", type=str, help="eg: 2024_input_dir")
    parser.add_argument("--s3_output_folder", type=str, help="eg: 2024_output_dir")

    s3_bucket = parser.parse_args().s3_bucket
    s3_input_folder = parser.parse_args().s3_input_folder
    s3_ouput_folder = parser.parse_args().s3_output_folder

    print("s3_bucket:", s3_bucket)
    print("s3_input_folder:", s3_input_folder)
    print("s3_output_folder:", s3_ouput_folder)
    

    process_images(
        s3_bucket=s3_bucket,
        s3_input_folder=s3_input_folder,
        s3_output_folder=s3_ouput_folder
        )


 