import sys
from download_sentinel_images import download
import boto3
from datetime import datetime
import argparse

if __name__ == "__main__":


    session = boto3.Session()

    parser = argparse.ArgumentParser(description="MESMA Pipeline Entrypoint")

    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--tiles", type=str, help="Comma-separated list of MGRS tiles")
    parser.add_argument("--s3_bucket", type=str, help="eg: ce.sentinel2")
    parser.add_argument("--s3_folder", type=str, help="eg: 2024_input_dir")

    start_date = datetime.strptime(parser.parse_args().start_date, "%Y-%m-%d")
    end_date = datetime.strptime(parser.parse_args().end_date, "%Y-%m-%d")
    tiles_list = [tile.strip() for tile in parser.parse_args().tiles.split(",")]
    bands=['B02', 'B03', 'B04','B05', 'B06', 'B07','B08', 'B11',"B12"]
    bounds=[-120.708008, 33.156797, -113.975687 , 38.395343]
    s3_bucket = parser.parse_args().s3_bucket
    s3_folder = parser.parse_args().s3_folder

    print("Start date:", start_date)
    print("End date:", end_date)
    print("Tiles:", tiles_list)
    print("stage:", parser.parse_args().stage)
    download(
        session=session,
        start_date=start_date,
        end_date=end_date,
        mgrs_grids = tiles_list,
        bands=bands,
        bounds=bounds,
        s3_bucket=s3_bucket,
        s3_folder=s3_folder
        )


 