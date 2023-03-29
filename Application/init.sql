create database if not exists organic_integrity;
GRANT SELECT, INSERT, UPDATE, DELETE ON organic_integrity.organic_item TO flaskuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON organic_integrity.organic_operation TO flaskuser;
