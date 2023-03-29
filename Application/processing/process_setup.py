# process_setup.py
# This file handles xml read, file conversion, and database import for the organic integrity data
# The sqlalchemy database import section and argparsing is derived from:
# https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/week_1_basics_n_setup/2_docker_sql/ingest_data.py

import argparse
import datetime
import integrity_all_data_get
import logging
import json
import organic_xml_import
from os import getenv, path, sep
import pandas as pd
from sqlalchemy import create_engine
import time
import organic_processing


def api_call(processing_path):
# Use three trials separated by 5 minutes for data retrieval from API.
    trials = 0
    status = -1
    while trials < 3 and status != 0:
        status = integrity_all_data_get.integrity_all_data_get(processing_path=processing_path)
        if status != 0:
            time.sleep(2*60)
        trials = trials + 1
    return status


def world_process_wrapper():
    organic_processing.world_process()

def us_process_wrapper():
    organic_processing.us_process()

def products_process_wrapper():
    organic_processing.products_process()

def us_forecasting_process_wrapper():
    organic_processing.us_forecasting_process()


# Keep a separate record of the last run date.
def last_run_date(mode="R"):
    processing_path = getenv("PROCESSING_PATH")
    if processing_path is None:
        processing_path = f"{sep}Application{sep}processing{sep}"
    if mode == "R":
        try:
            with open(processing_path + "last_date.txt", "r") as f:
                last_run = f.readline().rstrip()
            last_run = datetime.datetime.strptime(last_run, "%Y-%m-%d")
        except FileNotFoundError:
            last_run = None
    else:
        last_run = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
        with open(processing_path + "last_date.txt", "w") as f:
            f.write(last_run)
        
    return last_run


def main(params):
    USE_EXISTENT = params.use_existent if params.use_existent in ["Y", "N"] else "Y"
    SCHEDULED_RUN = params.scheduled_run if params.scheduled_run in ["Y", "N"] else "Y"
    process_setup(USE_EXISTENT=USE_EXISTENT, SCHEDULED_RUN=SCHEDULED_RUN)


def process_setup(USE_EXISTENT="Y", SCHEDULED_RUN='Y'):
    # Start logging
    processing_path = getenv("PROCESSING_PATH")
    if processing_path is None:
        processing_path = f"{sep}Application{sep}processing{sep}"

    logging.basicConfig(filename=processing_path+"integrity_app_dag_log.log", format="%(asctime)s - %(message)s", level=logging.INFO)
    logging.info(f"Integrity App pipeline start. Option use_existent: {USE_EXISTENT}. Option scheduled_run: {SCHEDULED_RUN}")

    interval_passed = False
    last_run = last_run_date(mode="R")
    if last_run is None:
        interval_passed = True
    elif (datetime.datetime.now() - last_run) / datetime.timedelta(days = 1) >= 14:
        interval_passed = True
    else:
        interval_passed = False

    if SCHEDULED_RUN == 'Y' and interval_passed is False:
        logging.info("Integrity App pipeline start. Started on scheduled_run; schedule interval not passed.")
        print("Scheduled run interval not passed.")
        return 0

#--------------------- api_call -----------------------------------
    try:
        if USE_EXISTENT == "N":
            logging.info(f"api_call node running.")
            status = api_call(processing_path=processing_path)
            if status != 0:
                print("API data could not be retrieved!")
                return 1
    except Exception as e:
        logging.error(f"api_call node error: {e}.")
        return 1
    logging.info(f"api_call node completed.")

#--------------------- xml_to_db -----------------------------------

    logging.info(f"xml_to_db node running.")
    try:
        organic_import = organic_xml_import.xml_to_mysql()
        organic_import.xml_import()
    except Exception as e:
        logging.error(f"xml_to_db node error: {e}.")
        return 1
    logging.info(f"xml_to_db node completed.")
    
#--------------------- world_process_wrapper -----------------------------------

    logging.info(f"world_process_wrapper node running.")
    try:
        world_process_wrapper()
    except Exception as e:
        logging.error(f"world_process_wrapper node error: {e}.")
        return 1
    logging.info(f"world_process_wrapper node completed.")

#--------------------- us_process_wrapper -----------------------------------

    logging.info(f"us_process_wrapper node running.")
    try:
        us_process_wrapper()
    except Exception as e:
        logging.error(f"us_process_wrapper node error: {e}.")
        return 1
    logging.info(f"us_process_wrapper node completed.")

#--------------------- products_process_wrapper -----------------------------------

    logging.info(f"products_process_wrapper node running.")
    try:
        products_process_wrapper()
    except Exception as e:
        logging.error(f"products_process_wrapper node error: {e}.")
        return 1
    logging.info(f"products_process_wrapper node completed.")

#--------------------- us_forecasting_process_wrapper -----------------------------------

    logging.info(f"us_forecasting_process_wrapper node running.")
    try:
        us_forecasting_process_wrapper()
    except Exception as e:
        logging.error(f"us_forecasting_process_wrapper node error: {e}.")
        return 1
    logging.info(f"us_forecasting_process_wrapper node completed.")

#------ Finalize ---------------
    print("Pipeline completed!")
    last_run_date(mode="W")
    return 0


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Integrity API - DB workflow")

    # user, password, host, port, db name, table name, csv url.

    help_txt_s="'Y' to only run if interval has passed, 'N' to run regardless'"

    help_txt_u="'Y' to use existent xml files, 'N' to request from organic integrity API.'"

    parser.add_argument("--use_existent", help=help_txt_u, default="N")
    parser.add_argument("--scheduled_run", help=help_txt_s, default="Y")

    args = parser.parse_args()

    main(args)