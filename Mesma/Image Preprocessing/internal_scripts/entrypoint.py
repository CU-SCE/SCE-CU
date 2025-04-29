import sys
from image_processing import process_images
import boto3
from datetime import datetime
import argparse
import os

def list_files_and_folders(directory):
    """Lists all files and folders in the given directory."""
    try:
        items = os.listdir(directory)
        for item in items:
            print(item)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":


    session = boto3.Session()

    parser = argparse.ArgumentParser(description="MESMA Pipeline Entrypoint")

    parser.add_argument("stage", choices=["download", "preprocess", "mesma"], help="Stage to run")
    
    parser.add_argument("--s3_bucket", type=str, help="eg: sce.sentinel2")
    parser.add_argument("--s3_input_folder", type=str, help="eg: 2024_input_dir")
    parser.add_argument("--s3_output_folder", type=str, help="eg: 2024_output_dir")

    s3_bucket = parser.parse_args().s3_bucket
    s3_input_folder = parser.parse_args().s3_input_folder
    s3_ouput_folder = parser.parse_args().s3_output_folder

    print("s3_bucket:", s3_bucket)
    print("s3_input_folder:", s3_input_folder)
    print("s3_output_folder:", s3_ouput_folder)
    print("stage:", parser.parse_args().stage)

    list_files_and_folders("/workspace/")
    
    if parser.parse_args().stage == "preprocess":
        process_images(
            s3_bucket=s3_bucket,
            s3_input_folder=s3_input_folder,
            s3_output_folder=s3_ouput_folder
            )
    else:
        raise ValueError("Unknown stage")

 