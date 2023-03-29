import xml.etree.ElementTree as ET
import pandas as pd
from mysql import connector
import os
from sqlalchemy import create_engine, select
from sqlalchemy.types import String, DateTime
import sys
import process_db_model
from sqlalchemy.sql.functions import coalesce, count
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session, scoped_session, sessionmaker

class xml_to_mysql():

    def __init__(self, chunk_len=10000):
        # project directory
        file_dir = os.path.dirname(os.path.abspath(__file__))

        # Read in the xml file.
        tree = ET.parse(file_dir + "/integrity_download/stream.xml")

        self.root = tree.getroot()
        
        self.SessionMaker = sessionmaker(bind=process_db_model.engine)

        self.table_name_alchemy_map = process_db_model.table_name_alchemy_map

        self.CHUNK_LEN = chunk_len
    # This method extracts from xml and returns a dataframe.
    ## Assumes no elements past the first two levels are nested, as matches the specifications.
    #def xml_to_pd(self, subroot_name):
    #    xml_data=self.root[self.root_level]
    #    record_list = list()
    #    pk_found = True
    #    for entry in xml_data.findall(subroot_name):
    #        record=dict()
    #        if self.primary_key is not None:
    #            pk_found = False
    #        for col in self.dtypes.keys():ex
    #            try:
    #                record[col] = entry.find(col).text
    #                if col == self.primary_key:
    #                    pk_found = True
    #            except AttributeError:
    #                record[col] = None
    #        if pk_found is True:
    #            record_list.append(record)
    #    return record_list
#
    #def table_insert(self):
    #    record_chunk_start = 0
    #    record_chunk_end = self.CHUNK_LEN
    #    records_left = True
    #    while records_left is True:
    #        with self.SessionMaker() as session:
    #            session.bulk_insert_mappings(self.table_name_alchemy_map[self.output_table_name],
    #            self.record_list[record_chunk_start:record_chunk_end])
    #            session.commit()
    #        if record_chunk_end >= len(self.record_list):
    #            records_left = False
    #        else:
    #            record_chunk_start = record_chunk_end
    #            record_chunk_end = record_chunk_end + self.CHUNK_LEN
#


    def xml_to_db(self, subroot_name):
        xml_data=self.root[self.root_level]
        record_list = list()
        pk_found = True
        for entry in xml_data.findall(subroot_name):
            record=dict()
            if self.primary_key is not None:
                pk_found = False
            for col in self.dtypes.keys():
                try:
                    record[col] = entry.find(col).text
                    if col == self.primary_key:
                        pk_found = True
                except AttributeError:
                    record[col] = None
            if pk_found is True:
                record_list.append(record)
            
            if len(record_list) == self.CHUNK_LEN:
                self.table_insert(record_list)
                record_list = list()

        if len(record_list) > 0:
            self.table_insert(record_list)


    def table_insert(self, record_list):
        with self.SessionMaker() as session:
            session.bulk_insert_mappings(self.table_name_alchemy_map[self.output_table_name],
            record_list)
            session.commit()

    def table_delete(self):
        with self.SessionMaker() as session:
            session.query(self.table_name_alchemy_map[self.output_table_name]).delete()
            session.commit()


    def xml_import(self):
        # Get column and table information, extract data, and write to csv files.
        for table_name in process_db_model.xml_table_name_map.keys():
            self.output_table_name = process_db_model.xml_table_name_map[table_name][0]
            self.root_level = process_db_model.xml_table_name_map[table_name][1]
            self.primary_key = process_db_model.xml_table_name_map[table_name][2]
            self.dtypes = dict()
            for col_name in process_db_model.col_dict.keys():
                if self.output_table_name in col_name:
                    short_col_name = col_name.split(".", maxsplit=1)[1]
                    self.dtypes[short_col_name] = process_db_model.col_dict[col_name]

            date_col_list = list()
            for k, v in self.dtypes.items():
                if v == "datetime":
                    self.dtypes[k] = "str"
                    date_col_list.append(k)

            self.table_delete()
            self.xml_to_db(subroot_name=table_name)
            #
            # self.xml_to_pd(subroot_name=table_name)
            # self.record_list = self.xml_to_pd(subroot_name=table_name)
            # print("Record list completed")
            # self.table_delete()
            # print(f"Table {self.output_table_name} deleted")
            # self.table_insert()
            # print(f"Record list inserted into {self.output_table_name}")


if __name__ == "__main__":
    organic_xml_import = xml_to_mysql()
    organic_xml_import.xml_import()

    #for file in file_dict.keys():
    #    print(f"{file} at: {file_dict[file]}")