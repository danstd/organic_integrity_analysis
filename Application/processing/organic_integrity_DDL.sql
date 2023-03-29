drop table if exists organic_item;
drop table if exists organic_operation;

create table organic_operation (
op_artID BIGINT NOT NULL AUTO_INCREMENT,  -- Artificial primary key added in.
op_certifierName VARCHAR(256),
op_nopOpID BIGINT NOT NULL,
op_name VARCHAR(256),
op_clientID VARCHAR(256),
op_contFirstName VARCHAR(256),
op_contLastName VARCHAR(256),
op_status VARCHAR(256),
op_statusEffectiveDate DateTime,
op_nopAnniversaryDate DateTime,
op_lastUpdatedDate DateTime,
opSC_CR VARCHAR(256),
opSC_CR_ED DateTime,
opSC_LS VARCHAR(256),
opSC_LS_ED DateTime,
opSC_WC VARCHAR(256),
opSC_WC_ED DateTime,
opSC_HANDLING VARCHAR(256),
opSC_HANDLING_ED DateTime,
opPA_line1 VARCHAR(256),
opPA_line2 VARCHAR(256),
opPA_city VARCHAR(256),
opPA_state VARCHAR(256),
opPA_country VARCHAR(256),
opPA_zip VARCHAR(256),
opPA_countyCode VARCHAR(256),
opPA_county VARCHAR(256),
opMA_line1 VARCHAR(256),
opMA_line2 VARCHAR(256),
opMA_city VARCHAR(256),
opMA_state VARCHAR(256),
opMA_country VARCHAR(256),
opMA_zip VARCHAR(256),
opMA_countyCode VARCHAR(256),
opMA_county VARCHAR(256),
op_phone VARCHAR(256),
op_email VARCHAR(256),
op_url VARCHAR(256),
op_opExtraInfo VARCHAR(256),
opEx_broker VARCHAR(256),
opEx_csa VARCHAR(256),
opEx_copacker VARCHAR(256),
opEx_dairy VARCHAR(256),
opEx_distributor VARCHAR(256),
opEx_marketerTrader VARCHAR(256),
opEx_restaurant VARCHAR(256),
opEx_retailer VARCHAR(256),
opEx_poultry VARCHAR(256),
opEx_privateLabeler VARCHAR(256),
opEx_slaughterHouse VARCHAR(256),
opEx_storage VARCHAR(256),
opEx_growerGroup VARCHAR(256),
opCert_url VARCHAR(256),
PRIMARY KEY (op_artID),
INDEX (op_nopOpID)
);


create table organic_item (
ci_artID BIGINT NOT NULL AUTO_INCREMENT,  -- Artificial primary key added in.
ci_nopOpID BIGINT NOT NULL,
ci_certNumber VARCHAR(256),
ci_nopScope VARCHAR(256),
ci_nopCategory VARCHAR(256),
ci_nopCatID VARCHAR(256),
ci_nopCatName VARCHAR(256),
ci_nopItemID VARCHAR(256),
ci_itemList VARCHAR(4096),
ci_varieties VARCHAR(4096),
ci_status VARCHAR(256),
ci_statusEffectiveDate DATETIME,
ci_organic100 VARCHAR(256),
ci_organic VARCHAR(256),
ci_madeWithOrganic VARCHAR(256),
PRIMARY KEY (ci_artID),
INDEX (ci_nopOpID),
CONSTRAINT fk_operation_ID FOREIGN KEY (ci_nopOpID) REFERENCES organic_operation(op_nopOpID) ON DELETE CASCADE




);