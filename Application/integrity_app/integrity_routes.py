
from integrity_app import app
from flask import Flask, redirect, render_template, request, url_for, jsonify
import pandas as pd
import plotly
import datetime
import json
from os import sep, getenv
import subprocess
import sys

# Set file path variables
# Having issues with path recognition on pythonanywhere.
#if sys.platform == "win32":
#    STATIC = "integrity_app" + sep + "static" + sep
#    STATIC_IMG = "integrity_app" + sep + "static" + sep + "images" + sep
#else:
#    STATIC = "/home/ddavis11/mysite/integrity_app/static/"
#    STATIC_IMG = "/home/ddavis11/mysite/integrity_app/static/images/"    
# Set file path variables
STATIC = "integrity_app/static/"
STATIC_IMG = "integrity_app/static/images/"

#app = Flask(__name__)
#app.debug = True

@app.route("/", methods=["GET"])
def index():
    if request.method != "GET":
        return render_template("organic_main_page.html")
    else:
        
        return render_template(
            "organic_main_page.html")
        
#----------------------world route---------------------
@app.route("/world", methods=["GET"])
def world():
    if request.method != "GET":
        return render_template("main_page.html")
    else:
        # Get saved images and csv files.
        country_table = pd.read_csv(STATIC + "op_status_country.csv")

        scopes_count = pd.read_csv(STATIC + "scopes_count.csv")
        scope_card_keys = scopes_count.columns.to_list()
        scope_card_vals = scopes_count.values.tolist()
        
        # Convert to dictionary so the result can easily be put into cards.
        scope_cards = dict()
        for i in range(0,len(scope_card_keys)):
            scope_cards[scope_card_keys[i]] = scope_card_vals[0][i]

        scope_set = pd.read_csv(STATIC + "scopes_combo.csv")
        scope_set = scope_set.fillna("")

        # Solve potential rounding issues.
        scope_set["Percentage"] = round(scope_set["Percentage"],3)

        # Read in plotly charts.
        with open(STATIC + "world_certification_status_trend.json") as j_stat_trend:
            world_certification_status_trend = json.dumps(plotly.io.from_json(j_stat_trend.read()), cls=plotly.utils.PlotlyJSONEncoder)

        with open(STATIC + "world_certification_change.json") as j_change:
            world_certification_change = json.dumps(plotly.io.from_json(j_change.read()), cls=plotly.utils.PlotlyJSONEncoder)

            #world_certification_status_trend = j.read()
        return render_template(
            "world.html",
            country_table=country_table.values.tolist(),
            country_table_cols=country_table.columns.to_list(),
            scope_cards=scope_cards,
            scopes_combo=scope_set.values.tolist(),
            scopes_combo_cols=scope_set.columns.to_list(),
            world_certification_status_trend=world_certification_status_trend,
            world_certification_change=world_certification_change
            )

#----------------------united_states route---------------------
@app.route("/united_states", methods=["GET"])
def united_states():
    if request.method != "GET":
        return render_template("main_page.html")
    else:
        # Get saved images and csv files.

        us_pivot = pd.read_csv(STATIC + "us_table.csv")
        us_pivot = us_pivot.fillna("")

        us_scopes_return = pd.read_csv(STATIC + "us_scopes_return.csv", dtype=str)
        # Must fix formatting
        for i in us_scopes_return.columns.to_list():
            us_scopes_return[i] = us_scopes_return[i].str.replace(".0","",regex=False)
            us_scopes_return[i] = us_scopes_return[i].str.replace("^0$","None",regex=True)

        us_scopes_return = us_scopes_return.fillna("")
        
        # Read in plotly charts.
        with open(STATIC + "us_certification_status_trend.json") as j_stat_trend:
            us_certification_status_trend = json.dumps(plotly.io.from_json(j_stat_trend.read()), cls=plotly.utils.PlotlyJSONEncoder)
        with open(STATIC + "us_certification_change.json") as j_change:
            us_certification_change = json.dumps(plotly.io.from_json(j_change.read()), cls=plotly.utils.PlotlyJSONEncoder)
        with open(STATIC + "us_certification_count.json") as j_count:
            us_certification_count = json.dumps(plotly.io.from_json(j_count.read()), cls=plotly.utils.PlotlyJSONEncoder)

        return render_template(
            "united_states.html",
            us_table=us_pivot.values.tolist(),
            us_table_cols=us_pivot.columns.to_list(),
            us_scopes_display=us_scopes_return.values.tolist(),
            us_certification_status_trend=us_certification_status_trend,
            us_certification_change=us_certification_change,
            us_certification_count=us_certification_count)


#----------------------products route---------------------
@app.route("/products", methods=["GET"])
def products():
    if request.method != "GET":
        return render_template("main_page.html")
    else:
        top_items_crops = pd.read_csv(STATIC + "top_items_crops.csv").values.tolist()
        top_items_livestock = pd.read_csv(STATIC + "top_items_livestock.csv").values.tolist()
        top_items_handling = pd.read_csv(STATIC + "top_items_handling.csv").values.tolist()
        top_items_wild = pd.read_csv(STATIC + "top_items_wild.csv").values.tolist()

        top_by_country = pd.read_csv(STATIC + "top_by_country.csv").values.tolist()

        top_by_country_scope = pd.read_csv(STATIC + "top_by_country_scope.csv")
        top_by_country_scope.fillna("",inplace=True)
        top_by_country_scope=top_by_country_scope.values.tolist()
        
        return render_template(
            "products.html",
            top_items_crops=top_items_crops,
            top_items_livestock=top_items_livestock,
            top_items_handling=top_items_handling,
            top_items_wild=top_items_wild,
            top_by_country=top_by_country,
            top_by_country_scope=top_by_country_scope)


#----------------------united_states route---------------------
@app.route("/us_forecasting", methods=["GET"])
def us_forecasting():
    if request.method != "GET":
        return render_template("main_page.html")
    else:
        # Read in plotly charts.
        with open(STATIC + "us_forecast_month_change.json") as j_forecast_change:
            us_forecast_month_change_json = json.dumps(plotly.io.from_json(j_forecast_change.read()), cls=plotly.utils.PlotlyJSONEncoder)   
        with open(STATIC + "us_forecast_count.json") as j_forecast_count:
            us_forecast_count_json = json.dumps(plotly.io.from_json(j_forecast_count.read()), cls=plotly.utils.PlotlyJSONEncoder)       
        
        return render_template("us_forecasting.html",
            us_forecast_month_change_json=us_forecast_month_change_json,
            us_forecast_count_json=us_forecast_count_json)
            


#----------------Processing route-------------------------
@app.route("/process", methods=["GET", "POST"])
def process():
    # Authenticate key
    headers = request.headers
    auth = headers.get("key")
    # if auth != key_get("integrity_app_process", file=KEY_PATH):
    if auth != getenv("FLASK_PROCESS_KEY").strip():
        #return jsonify({"message": "ERROR: Unauthorized"}), 401
        return jsonify({"message": "Not verified"}), 401
    if request.method != "POST":
        return "POST to run data pipeline"
    else:
        processing_path = getenv("PROCESSING_PATH")
        if processing_path is None:
            processing_path = f"{sep}Application{sep}processing{sep}"
        # For local testing: processing_path = "C:\\Users\\daniel\\Documents\\organic_env\\organic_integrity_flask\\Application\\processing\\"
        subprocess.call(["python", processing_path+"process_setup.py", "--use_existent", "Y"])


        return "Processing is in progress"
