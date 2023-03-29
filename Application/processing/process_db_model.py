from sqlalchemy import create_engine
import pandas as pd
import datetime
from os import sep, getenv

# From flask info: https://github.com/pallets/website
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, \
     ForeignKey, event
from sqlalchemy.orm import backref, relation, relationship
from sqlalchemy.ext.declarative import declarative_base

USERNAME = getenv("MYSQL_USER")
PSWD = getenv("MYSQL_ROOT_PASSWORD")
HOST = getenv("HOST")
DB = getenv("DATABASE_NAME")

engine = create_engine(f"mysql+mysqlconnector://{USERNAME}:{PSWD}@{HOST}/{DB}")

# db_session = scoped_session(sessionmaker(autocommit=False,
#                                          autoflush=False,
#                                          bind=engine))
# 
# #def init_db():
# #    Model.metadata.create_all(bind=engine)
# 
Model = declarative_base(name='Model')
Model.metadata.create_all(bind=engine)
# 
# Model.query = db_session.query_property()

class OrganicOperation(Model):
    __tablename__ = "organic_operation"
    op_artID = Column(Integer, primary_key=True) # Artificial primary key added in.
    op_certifierName = Column(String(256))
    op_nopOpID = Column(String(256))
    op_name = Column(String(256))
    #op_otherNames = Column(String(256))
    op_clientID = Column(String(256))
    op_contFirstName = Column(String(256))
    op_contLastName = Column(String(256))
    op_status = Column(String(256))
    op_statusEffectiveDate = Column(DateTime)
    op_nopAnniversaryDate = Column(DateTime)
    op_lastUpdatedDate = Column(DateTime)
    opSC_CR = Column(String(256))
    opSC_CR_ED = Column(DateTime)
    opSC_LS = Column(String(256))
    opSC_LS_ED = Column(DateTime)
    opSC_WC = Column(String(256))
    opSC_WC_ED = Column(DateTime)
    opSC_HANDLING = Column(String(256))
    opSC_HANDLING_ED = Column(DateTime)
    opPA_line1 = Column(String(256))
    opPA_line2 = Column(String(256))
    opPA_city = Column(String(256))
    opPA_state = Column(String(256))
    opPA_country = Column(String(256))
    opPA_zip = Column(String(256))
    opPA_countyCode = Column(String(256))
    opPA_county = Column(String(256))
    opMA_line1 = Column(String(256))
    opMA_line2 = Column(String(256))
    opMA_city = Column(String(256))
    opMA_state = Column(String(256))
    opMA_country = Column(String(256))
    opMA_zip = Column(String(256))
    opMA_countyCode = Column(String(256))
    opMA_county = Column(String(256))
    op_phone = Column(String(256))
    op_email = Column(String(256))
    op_url = Column(String(256))
    # op_opExtraInfo = Column(String(256))
    opEx_broker = Column(String(256))
    opEx_csa = Column(String(256))
    opEx_copacker = Column(String(256))
    opEx_dairy = Column(String(256))
    opEx_distributor = Column(String(256))
    opEx_marketerTrader = Column(String(256))
    opEx_restaurant = Column(String(256))
    opEx_retailer = Column(String(256))
    opEx_poultry = Column(String(256))
    opEx_privateLabeler = Column(String(256))
    opEx_slaughterHouse = Column(String(256))
    opEx_storage = Column(String(256))
    opEx_growerGroup = Column(String(256))
    opCert_url = Column(String(256))


organic_item_artificial_key = "ci_artID"

class OrganicItem(Model):
    __tablename__ = "organic_item"
    ci_artID = Column(Integer, primary_key=True) # Artificial primary key added in.
    ci_nopOpID = Column(String(256), ForeignKey(OrganicOperation.op_nopOpID))
    ci_certNumber = Column(String(256))
    ci_nopScope = Column(String(256))
    ci_nopCategory = Column(String(256))
    ci_nopCatID = Column(String(256))
    ci_nopCatName = Column(String(256))
    ci_nopItemID = Column(String(256))
    ci_itemList = Column(String(4096))
    ci_varieties = Column(String(4096))
    ci_status = Column(String(256))
    ci_statusEffectiveDate = Column(String(256))
    ci_organic100 = Column(String(256))
    ci_organic = Column(String(256))
    ci_madeWithOrganic = Column(String(256))
    opPA_country = Column(String(256))
    fk_operation_ID = relationship("OrganicOperation", foreign_keys=ci_nopOpID)


# Map schema to pandas.
type_map = {
    "DATETIME": "datetime",
    "VARCHAR": "str",
    'INTEGER': "int",
    "FLOAT": "float"
}
col_dict = dict()

for table in [OrganicItem, OrganicOperation]:
    cols = table.__table__.columns
    for col in cols:
        col_dict[col.__str__()] = type_map[col.type.__str__().split("(", maxsplit=1)[0]]

xml_table_name_map = {
    "Operation": ["organic_operation", 0, "op_nopOpID"],
    "Item": ["organic_item", 1, None]
}

table_name_alchemy_map = {
    "organic_operation": OrganicOperation,
    "organic_item": OrganicItem
}

