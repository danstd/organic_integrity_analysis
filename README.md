# USDA Organic Integrity Database Analytics Dashboard
A full-stack Flask application for analytics on USDA National Organic Program certification

This project is a Flask application that shows analytics on USDA National Organic Program certification data. Through a scheduled data pipeline, XML data is ingested from the USDA Organic Integrity Database API and loaded into a MySQL database which is then accessed using SqlAlchemy. 
Chart/graph visualizations are created using Plotly, and functionality is added to tables using the DataTables Javascript plugin on the front end.
This project is live at organic-certification-analysis.com, and is hosted through PythonAnywhere.
