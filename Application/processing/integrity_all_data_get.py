# This script gets all operation data in an xml file from the Organic Integrity API.
# Set to work with windows (doubled backslashes)

import requests
import os
import shutil
from zipfile import ZipFile, BadZipFile
import sys
import datetime
import csv
import wget
# Delete folders from current directory containing folder_name variable
# if there are more than 5. Set to delete based on sorting by file name - works with standardized timestamp suffix.
def backup_manage(folder_name, backup_num, FILE_DIR):
    file_list = list()
    for i in os.listdir(FILE_DIR):
        if folder_name in i:
            file_list.append(i)
            
    if len(file_list) > backup_num:
        file_list.sort(reverse=True)

        for i in file_list[backup_num:]:
            shutil.rmtree(FILE_DIR + "/" + i)


def integrity_all_data_get(processing_path=None):
    if processing_path is None:
        processing_path = f"{os.sep}Application{os.sep}processing{os.sep}"
    # project directory
    #FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    FILE_DIR = processing_path
    # File path for holding download and xml file.
    DWNLD_NAME = "integrity_download"
    DWNLD_DIR = FILE_DIR + DWNLD_NAME

    replace_flag = False

    # If this data was retrieved, rename its directory with a timestamp. Make a new directory with the base name in DWNLD_DIR.
    if DWNLD_NAME in os.listdir(FILE_DIR):
        # Get timestamp to mark currently existing directory, if any.
        timestamp = datetime.datetime.strftime(datetime.datetime.today(),'%Y-%m-%d %H-%M-%S')
        # Rename the existing directory with the timestamp
        #os.rename(DWNLD_DIR, DWNLD_DIR + " replaced " + timestamp)
        shutil.move(DWNLD_DIR, DWNLD_DIR + " replaced " + timestamp)

        # Make sure more than 5 of these backups are not maintained.
        backup_manage(folder_name=DWNLD_NAME, backup_num=5, FILE_DIR=FILE_DIR)
        
        # Mark if the name change was done, in case of exceptions.
        replace_flag = True
        
    os.makedirs(DWNLD_DIR)

    # Get the xml data from the Integrity API.
    #end_point = "https://organicapi.ams.usda.gov/IntegrityPubDataServices/OidPublicDataService.svc/rest/GetAllOperationsPublicData?api_key="
    end_point = "end_point = "https://organicapi.ams.usda.gov/IntegrityPubDataServices/OIDPublicAPI/GetAllOperationsPublicData?api_key="
    end_point = end_point + os.getenv("INTEGRITY_API_KEY")

    integrity_zip = DWNLD_DIR + "/" + "integrity_xml.zip"

    print(f"File destination: {integrity_zip}\n")
    print(end_point)
    try:
        #r = requests.get(end_point, stream=True)
        #with open(integrity_zip, 'wb') as file:
        #    shutil.copyfileobj(r.raw, file)
        wget.download(url=end_point, out=integrity_zip)
    #except requests.ConnectionError as er:
    except Exception as er:
        print("A connection error occured!")
        print(er)
        # Remove the new download directory.
        shutil.rmtree(DWNLD_DIR)
    
        # If there was an existing download directory that was renamed with a timestamp, change the directory name back.
        if replace_flag:
            #os.rename(DWNLD_DIR + " replaced " + timestamp, DWNLD_DIR)
            shutil.move(DWNLD_DIR + " replaced " + timestamp, DWNLD_DIR)    
        return 1

    try:
        # Extract from the downloaded ZIP file.
        with ZipFile(integrity_zip, "r") as z:
            z.extractall(DWNLD_DIR)

            # Delete the zip file after extraction.
        os.remove(integrity_zip)

        # Contents are downloading without file extension. If this is the case add the xml extension.
        for i in os.listdir(DWNLD_DIR):
            if i == "stream":
                os.rename(DWNLD_DIR + "/" + i, DWNLD_DIR + "/" + "stream.xml")

    except BadZipFile:
        print("Zip file did not download correctly.")
        # Remove the new download directory.
        shutil.rmtree(DWNLD_DIR)

        # If there was an existing download directory that was renamed with a timestamp, change the directory name back.
        if replace_flag:
           # os.rename(DWNLD_DIR + " replaced " + timestamp, DWNLD_DIR)
            shutil.move(DWNLD_DIR + " replaced " + timestamp, DWNLD_DIR)
        
        return 1
    
    return 0

if __name__ == "__main__":
    integrity_all_data_get()
        
