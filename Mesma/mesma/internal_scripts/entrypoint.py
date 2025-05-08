import sys
from build_mesma_images import build
import boto3
from datetime import datetime
import argparse
import os

if __name__ == "__main__":


    session = boto3.Session()

    parser = argparse.ArgumentParser(description="MESMA Pipeline Entrypoint")

    parser.add_argument("--s3_bucket", type=str, help="eg: sce.sentinel2")
    parser.add_argument("--s3_output_folder", type=str, help="eg: 2024_output_dir")
    parser.add_argument("--image_files", type=str, help="eg: file1.tif,file2.tif")

    s3_bucket = parser.parse_args().s3_bucket
    image_files = [file.strip() for file in parser.parse_args().image_files.split(",")]
    s3_output_folder = parser.parse_args().s3_output_folder

    print("s3_bucket:", s3_bucket)
    print("image_files:", image_files)
    print("s3_output_folder:", s3_output_folder)

    build(
        s3_bucket=s3_bucket,
        # image_files=image_files,
        image_files=image_files,
        s3_output_folder=s3_output_folder,
        parser =parser
        )

 