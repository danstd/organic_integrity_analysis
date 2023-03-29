#from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from flask import jsonify
#from flask_sqlalchemy import SQLAlchemy

import pandas as pd
import datetime
import plotly.express as px
import plotly
from os import getenv
from sqlalchemy.sql.functions import coalesce, count
#from integrity_app.api_key_get import key_get

import json
import joblib

# From flask info
#from sqlalchemy import create_engine, Column, Integer, String, DateTime, \
#     ForeignKey, event
#from sqlalchemy.orm import scoped_session, sessionmaker, backref, relation, relationship
#from sqlalchemy.ext.declarative import declarative_base

from process_db_model import engine, OrganicOperation, OrganicItem #, Model

# Set file path variables
STATIC = getenv("STATIC")
if STATIC is None:
    STATIC = "/Application/integrity_app/static/"
#static_r = sep + sep.join(["Application", "integrity_app", "static"]) + sep
STATIC_R = STATIC

STATIC_IMG = getenv("STATIC_IMG")
if STATIC_IMG is None:
    STATIC_IMG = "/Application/integrity_app/static/images/"

# Key verification: https://blog.ruanbekker.com/blog/2018/06/01/add-a-authentication-header-to-your-python-flask-app/

# Get list index by name; useful for pandas iloc.
def col_index(col_list, col):
    for i in range(0,len(col_list)):
        if col_list[i] == col:
            return i
    return ("not found")

#----------------World page processing-------------------------
def world_process():
    first_of_current_month =str( datetime.datetime.now().year) + "-" + str( datetime.datetime.now().month)
    first_of_current_month = datetime.datetime.strptime(first_of_current_month + "-1", "%Y-%m-%d")

    # op_status_country.csv------------------------
    # Query to get number of operations by status and by country
    with Session(engine) as session:
        op_return = session.query(
            OrganicOperation.opPA_country.label("Country"),
            OrganicOperation.op_status,
            count(OrganicOperation.op_nopOpID).label("op_count")
            ).select_from(OrganicOperation).order_by(OrganicOperation.opPA_country).group_by(
            OrganicOperation.opPA_country,
            OrganicOperation.op_status
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        # Pivot the result by certification status
        country_table = pd.DataFrame(op_return).pivot_table(
            index="Country",
            columns="op_status",
            values="op_count",
            aggfunc="sum", fill_value=0,
            margins=True)

        country_table.reset_index(inplace=True)

        # Change names for formatting - put entries without a country listed last, and the summary row first.
        country_table.loc[country_table["Country"]=="", "Country"] = "__No Country Name"
        country_table.loc[country_table["Country"]=="All", "Country"] = "AAALL"

        country_table["Country"] = country_table["Country"].str.replace("the", "The", regex=False)

        country_table.sort_values("Country",inplace=True)
        country_table.loc[country_table["Country"]=="AAALL", "Country"] = " All Countries"
        country_table.loc[country_table["Country"]=="__No Country Name", "Country"] = " No Country Name"

        country_table.to_csv(STATIC + "op_status_country.csv", index=False)

        # world_certification_status_trend.json---------------------------
        # Create certification change plot.
    with Session(engine) as session:
        certification_date = session.query(
            OrganicOperation.op_statusEffectiveDate,
            OrganicOperation.op_status,
            count(OrganicOperation.op_nopOpID).label("op_count")
            ).select_from(OrganicOperation).group_by(
            OrganicOperation.op_statusEffectiveDate,
            OrganicOperation.op_status).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        cert_date_df = pd.DataFrame(certification_date)
        # Get dataframe copy for world_certification_change
        trend_df = cert_date_df.copy()
        cert_date_df["year"] = pd.DatetimeIndex(cert_date_df["op_statusEffectiveDate"]).year
        cert_date_df.rename(columns={"op_status": "Certification Status"}, inplace=True)


    # Further aggregate by month
    cert_date_df["op_statusEffectiveDate"] = cert_date_df["op_statusEffectiveDate"].apply(lambda x: x.replace(day=1))

    cert_date_df = cert_date_df.loc[cert_date_df["year"] > datetime.datetime.now(
        ).year-10].groupby(["Certification Status","op_statusEffectiveDate"], as_index=False)["op_count"].sum().reset_index()

    fig = px.line(cert_date_df,
        x="op_statusEffectiveDate",
        y="op_count",
        color="Certification Status",
        markers=True,
        labels={
            "op_statusEffectiveDate":"Date",
            "op_count":"Monthly Total"
        })

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    certification_date_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "world_certification_status_trend.json", "w") as j:
        j.write(certification_date_json)

    # world_certification_change.json---------------------
    # Create basic certification change plot - certified minus surrendered, suspended, etc..
    trend_df['year'] = pd.DatetimeIndex(trend_df['op_statusEffectiveDate']).year
    trend_df['op_statusEffectiveDate'] = trend_df['op_statusEffectiveDate'].apply(lambda x: x.replace(day=1))
    trend_df = trend_df.loc[trend_df['year'] > 2018].copy()
    trend_df = trend_df.loc[trend_df["op_status"] != "Applied; APEDA Certified"].copy()

    # Group by operation count.
    trend_df = trend_df.groupby(['op_status','op_statusEffectiveDate'], as_index=False)['op_count'].sum().reset_index()

    # Pivot result on operation status
    trend_df = trend_df.pivot_table(
        index="op_statusEffectiveDate",
        columns="op_status",
        values="op_count",
        aggfunc="sum", fill_value=0,
        margins=False)

    # Get the trend - count of certified minus surrendered, suspended, and revoked.
    trend_df["Trend"] = trend_df["Certified"] - (trend_df["Revoked"] + trend_df["Surrendered"] + trend_df["Suspended"])

    fig = px.line(trend_df.reset_index(drop=False),
        x="op_statusEffectiveDate",
        y="Trend",
        markers=True,
        labels={
            "op_statusEffectiveDate":"Date",
            "Trend":"Monthly Change"
        })

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    certification_change_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "world_certification_change.json", "w") as j:
        j.write(certification_change_json)

        # scopes_count.csv------------------------
        # Global certification scope get
        # Subqueries
    with Session(engine) as session:
        handling_count = session.query(
            count(OrganicOperation.opSC_HANDLING
            ).label("Handling")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opSC_HANDLING == "Certified"
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        crops_count = session.query(
            count(OrganicOperation.opSC_CR
            ).label("Crops")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opSC_CR == "Certified"
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        livestock_count = session.query(
            count(OrganicOperation.opSC_LS
            ).label("Livestock")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opSC_LS == "Certified"
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        wild_count = session.query(
            count(OrganicOperation.opSC_WC
            ).label("Wild_Crops")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opSC_WC == "Certified"
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month)

        # Union for single call to db.
        scopes_return = (handling_count
            ).union(crops_count
            ).union(livestock_count
                ).union(wild_count
            ).all()

        # Extract counts by scope.
        scopes = ["Handling", "Crops", "Livestock", "Wild Crops"]
        scopes_count = dict()
        for i in range(0,len(scopes)):
            scopes_count[scopes[i]]= scopes_return[i][0]

        pd.DataFrame(scopes_count, index=[0]).to_csv(STATIC + "scopes_count.csv", index=False)

        # scopes_combo.csv---------------------------------
        # Get certified count combinations
        # Get all scope certification columns
    with Session(engine) as session:
        scope_set = session.query(
            OrganicOperation.opSC_HANDLING,
            OrganicOperation.opSC_CR,
            OrganicOperation.opSC_LS,
            OrganicOperation.opSC_WC,
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).all()

        # Make a dataframe and drop any certifications that are not certified at all.
        scope_set = pd.DataFrame(scope_set, columns=["H", "C", "L", "W"])

    scope_set = scope_set.loc[
        (scope_set["H"] == "Certified") |
        (scope_set["C"] == "Certified") |
        (scope_set["L"] == "Certified") |
        (scope_set["W"] == "Certified")].copy()

    # Make a pseudo sparse matrix
    scope_cols = scope_set.columns.tolist()
    for i in scope_cols:
        scope_set[i] = scope_set[i].str.replace("Surrendered","")
        scope_set[i] = scope_set[i].str.replace("Suspended","")
        scope_set[i] = scope_set[i].str.replace("Certified",i)

    scope_set = scope_set.fillna("")

    # Group the combinations.
    # Pandas on pythonanywhere is ignoring the as_index argument.
    # Added reset_index to fix. As a result 'size' column is named '0'
    scope_set = scope_set.groupby(["H", "C", "L", "W"], as_index=False).size().reset_index()
    # Make a name column with meaning for the combinations.
    #scope_set["Name"] = scope_set["H"] +  ", " + scope_set["C"] + ", " + scope_set["L"] + ", " + scope_set["W"]
    #scope_set["Name"] = scope_set["Name"].str.replace(r'^(, )+|(, )+$', "", regex=True)
    #scope_set["Name"] = scope_set["Name"].str.replace(r'(, )+', ", ", regex=True)

    # Fix size column name
    if 0 in scope_set.columns.to_list():
        scope_set.rename(columns={0:"size"}, inplace=True)

    # Get the percentage of each combination.
    total = sum(scope_set["size"])

    scope_set["size"] = round(((scope_set["size"] / total)* 100),3)

    scope_set.sort_values("size", ascending=False, inplace=True)

    scope_set = scope_set[["size", "H", "C", "L", "W"]]

    scope_set.rename(
        columns={"size":"Percentage",
                "H":"Handling (H)",
                    "C":"Crops (C)",
                    "L":"Livestock (L)",
                    "W":"Wild Crops (W)"}
        , inplace=True)
    #scopes_combo_cols=["Handling (H)", "Crops (C)", "Livestock (L)", "Wild Crops (W)", "Percentage"]

    scope_set = scope_set.fillna("")

    scope_set.to_csv(STATIC + "scopes_combo.csv", index=False)

    return "The world view data was processed!"


#------------------------------united_states page processing-------------------------------
def us_process():
    first_of_current_month =str( datetime.datetime.now().year) + "-" + str( datetime.datetime.now().month)
    first_of_current_month = datetime.datetime.strptime(first_of_current_month + "-1", "%Y-%m-%d")

    with Session(engine) as session:
        # us_table.csv--------------------------
        # Query to get number of operations by status and by state for US (and outlying islands)
        us_return = session.query(
            OrganicOperation.opPA_state.label("State"),
            OrganicOperation.op_status,
            count(OrganicOperation.op_nopOpID).label("op_count")
            ).select_from(OrganicOperation).order_by(OrganicOperation.opPA_state).group_by(
            OrganicOperation.opPA_state,
            OrganicOperation.op_status
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).all()
        us_pivot = pd.DataFrame(us_return)

    us_pivot = us_pivot.pivot_table(index="State",
        columns="op_status",
        values="op_count",
        aggfunc="sum", fill_value=0,
        margins=True)

    us_pivot.reset_index(inplace=True)

    us_pivot.to_csv(STATIC + "us_table.csv", index=False)

        # us_scopes_return.csv-------------------------
            # Query to get number of certified operations by scope for the US.
            # States subquery b/c lack of outer join
    with Session(engine) as session:
        states_sub = session.query(
            distinct(OrganicOperation.opPA_state
            ).label("State")).select_from(OrganicOperation
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).subquery()

        # Handling subquery
        handling_sub = session.query(
            OrganicOperation.opPA_state,
            count(OrganicOperation.opSC_HANDLING).label("Handling")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.opSC_HANDLING == "Certified"
            ).group_by(OrganicOperation.opPA_state
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).subquery()

        # Crops subquery
        crops_sub = session.query(
            OrganicOperation.opPA_state,
            count(OrganicOperation.opSC_CR).label("Crops")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.opSC_CR == "Certified"
            ).group_by(OrganicOperation.opPA_state
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).subquery()

        # Livestock subquery
        livestock_sub = session.query(
            OrganicOperation.opPA_state,
            count(OrganicOperation.opSC_LS).label("Livestock")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.opSC_LS == "Certified"
            ).group_by(OrganicOperation.opPA_state
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).subquery()

        # Wild crops subquery
        wild_sub = session.query(
            OrganicOperation.opPA_state,
            count(OrganicOperation.opSC_WC).label("Wild_Crops")
            ).select_from(OrganicOperation
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.opSC_WC == "Certified"
            ).group_by(OrganicOperation.opPA_state
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).subquery()

        # Outer query
        us_scopes_return = session.query(
            states_sub.c.State,
            handling_sub.c.Handling,
            crops_sub.c.Crops,
            livestock_sub.c.Livestock,
            wild_sub.c.Wild_Crops
            ).select_from(states_sub
            ).join(handling_sub, states_sub.c.State == handling_sub.c.opPA_state, isouter=True
            ).join(crops_sub, states_sub.c.State == crops_sub.c.opPA_state, isouter=True
            ).join(livestock_sub, states_sub.c.State == livestock_sub.c.opPA_state, isouter=True
            ).join(wild_sub, states_sub.c.State == wild_sub.c.opPA_state, isouter=True
            ).all()

        us_scopes_return = pd.DataFrame(us_scopes_return).fillna("0")

    us_scopes_return.to_csv(STATIC + "us_scopes_return.csv", index=False)

        # us_certification_date.png------------------------------
        # Create US certification change plot.
    with Session(engine) as session:
        us_date = session.query(
            OrganicOperation.op_statusEffectiveDate,
            OrganicOperation.op_status,
            count(OrganicOperation.op_nopOpID).label("op_count")
            ).select_from(OrganicOperation).group_by(
            OrganicOperation.op_statusEffectiveDate,
            OrganicOperation.op_status
            ).filter(OrganicOperation.opPA_country.like("%United States%")
            ).filter(OrganicOperation.op_lastUpdatedDate < first_of_current_month
            ).all()

        us_date_df = pd.DataFrame(us_date)
        # For US trends
        trend_df = us_date_df.copy()

    us_date_df["year"] = pd.DatetimeIndex(us_date_df["op_statusEffectiveDate"]).year

    us_date_df.rename(columns={"op_status": "Certification Status"}, inplace=True)

    # Further aggregate by month
    us_date_df["op_statusEffectiveDate"] = us_date_df["op_statusEffectiveDate"].map(lambda x: x.replace(day=1))

    us_date_df = us_date_df.loc[us_date_df["year"] > datetime.datetime.now().year-10
        ].groupby(["Certification Status","op_statusEffectiveDate"], as_index=False
        )["op_count"].sum().reset_index()

    fig = px.line(us_date_df,
        x="op_statusEffectiveDate",
        y="op_count",
        color="Certification Status",
        markers=True,
        labels={
            "op_statusEffectiveDate":"Date",
            "op_count":"Monthly Change"
        })

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    certification_trend_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "us_certification_status_trend.json", "w") as j:
        j.write(certification_trend_json)

    # us_certification_date_basic---------------------------
    # Create basic certification change plot - certified minus surrendered, suspended, etc..

    # Get current count of US certified operations
    global us_cert_current
    us_cert_current = sum(trend_df.loc[trend_df["op_status"]=="Certified","op_count"])

    # Function to apply in getting monthly certification count
    def trend_change(trend):
        global us_cert_current
        us_cert_current = us_cert_current - trend
        return us_cert_current

    trend_df['year'] = pd.DatetimeIndex(trend_df['op_statusEffectiveDate']).year
    trend_df['op_statusEffectiveDate'] = trend_df['op_statusEffectiveDate'].apply(lambda x: x.replace(day=1))
    trend_df = trend_df.loc[trend_df['year'] > 2018]
    trend_df = trend_df.loc[trend_df["op_status"] != "Applied; APEDA Certified"]

    trend_df = trend_df.groupby(['op_status','op_statusEffectiveDate'], as_index=False)['op_count'].sum().reset_index()

    trend_df = trend_df.pivot_table(
        index="op_statusEffectiveDate",
        columns="op_status",
        values="op_count",
        aggfunc="sum", fill_value=0,
        margins=False)

    trend_df["Trend"] = trend_df["Certified"] - (trend_df["Revoked"] + trend_df["Surrendered"] + trend_df["Suspended"])

    # Get total count of certified operations estimate per month
    # This will not necessarily capture changes to/from suspension accurately
    trend_df.sort_values("op_statusEffectiveDate", ascending=False, inplace=True)
    trend_df["total_count"] = trend_df["Trend"].apply(trend_change)
    trend_df.sort_values("op_statusEffectiveDate", ascending=True, inplace=True)

    fig = px.line(trend_df.reset_index(drop=False),
        x="op_statusEffectiveDate",
        y="Trend",
        markers=True,
        labels={
            "op_statusEffectiveDate":"Date",
            "Trend":"Monthly Change"
        })

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    certification_change_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "us_certification_change.json", "w") as j:
        j.write(certification_change_json)

    fig = px.line(trend_df.reset_index(drop=False),
        x="op_statusEffectiveDate",
        y="total_count",
        markers=True,
        labels={
            "op_statusEffectiveDate":"Date",
            "total_count":"Certified Operations"
        })

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    certification_count_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "us_certification_count.json", "w") as j:
        j.write(certification_count_json)

    # Save US trend data for use in US forecasting route.
    trend_df.to_csv(STATIC + "us_trend_data.csv", index=True)

    return "The United States view data was processed!"


#----------------Products page route-------------------------
def products_process():
    first_of_current_month =str( datetime.datetime.now().year) + "-" + str( datetime.datetime.now().month)
    first_of_current_month = datetime.datetime.strptime(first_of_current_month + "-1", "%Y-%m-%d")

    with Session(engine) as session:
        country_items = session.query(
            coalesce(OrganicItem.ci_nopCatName,
            OrganicItem.ci_itemList,
            OrganicItem.ci_nopCategory),
            OrganicItem.ci_nopScope,
            OrganicOperation.opPA_country
            ).select_from(OrganicItem).join(OrganicOperation).filter(
            OrganicItem.ci_status == "Certified").all()
        #country_items = session.query(
        #    coalesce(OrganicItem.ci_nopCatName,
        #    OrganicItem.ci_itemList,
        #    OrganicItem.ci_nopCategory),
        #    OrganicItem.ci_nopScope,
        #    OrganicItem.opPA_country
        #    ).select_from(OrganicItem).filter(
        #    OrganicItem.ci_status == "Certified"
        #    ).filter(OrganicItem.ci_statusEffectiveDate < first_of_current_month
        #    ).all()

        items = pd.DataFrame(country_items, columns=["Items","Scope","Country"])

    items = items.loc[~items["Items"].isna()].copy()
            
    # Replace ampersand with comma
    items["Items"] = items["Items"].str.replace("&",",",False)

    # Convert to list of lists for iterating.
    items = items.values.tolist()

    # For each entry, separate on commas and add a new row (or nested list) for each separated entry
    item_new = list()

    for item in items:
        temp = item[0].split(",")
        for entry in temp:
            item_new.append([entry,item[1], item[2]])

    items = pd.DataFrame(item_new, columns=["Items","Scope","Country"])

    # Replace anything inside quotes. These are most likely brand names.
    items["Items"] = items["Items"].str.replace("[\"|\“|\”].*[\"|\“|\”]|[\"|\“|\”]","",regex=True)

    # Trim the items
    items["Items"] = items["Items"].str.strip()
    # Convert casing
    items["Items"] = items["Items"].str.lower()
    # Get rid of empty rows or rows consisting of some known adjectives.
    bad_items = ["",
    "natural",
    "dried",
    "packaging",
    "processing",
    "vegetables",
    "vegetable",
    "fruits",
    "fruit",
    "herbs",
    "herb",
    "oils"]
    items = items.loc[~(items["Items"].isin(bad_items))].copy()

        # Simple fix for displaying items neatly.
    def first_letter_fix(x):
        x = list(x)
        start = None
        for letter in range(len(x)):
            if x[letter].isalpha():
                start = letter
                break
        if start is not None:
            x = x[start:]
            x[0] = x[0].upper()
        x = "".join(x)
        return x

    items["Items"] = items["Items"].map(first_letter_fix)

    # Aggregate
    item_count = items.groupby(["Items","Scope"], as_index=False).size().reset_index()
    item_count.rename(columns={0:"size"}, inplace=True, errors="ignore")
    item_count.sort_values("size",ascending=False, inplace=True)

    item_count_c = item_count.loc[item_count["Scope"] == "Crops"].copy()
    item_count_l = item_count.loc[item_count["Scope"] == "Livestock"].copy()
    item_count_h = item_count.loc[item_count["Scope"] == "Handling"].copy()
    item_count_w = item_count.loc[item_count["Scope"] == "Wild Crops"].copy()

    item_index = col_index(item_count.columns.tolist(), "Items")
    size_index = col_index(item_count.columns.tolist(), "size")

    item_count_c.iloc[0:10,[item_index,size_index]].to_csv(STATIC + "top_items_crops.csv",index=False)
    item_count_l.iloc[0:10,[item_index,size_index]].to_csv(STATIC + "top_items_livestock.csv",index=False)
    item_count_h.iloc[0:10,[item_index,size_index]].to_csv(STATIC + "top_items_handling.csv",index=False)
    item_count_w.iloc[0:10,[item_index,size_index]].to_csv(STATIC + "top_items_wild.csv",index=False)

    # top_by_country.csv-------------
    country_item_agg = items.groupby(["Items","Country"],as_index=False).size().reset_index()
    if 0 in country_item_agg.columns.to_list():
        country_item_agg.rename(columns={0:"size"}, inplace=True)
    country_item_agg.sort_values("size", ascending=False, inplace=True)

    country_item_agg = country_item_agg.groupby("Country").head(1)
    country_item_agg.rename(columns={"size":"Count"}, inplace=True)
    country_item_agg = country_item_agg[["Country", "Items", "Count"]]
    country_item_agg.to_csv(STATIC + "top_by_country.csv",index=False)

    # top_by_country_scope.csv---------
    # Get count by country and scope
    country_item_scope_agg = items.groupby(["Items","Scope","Country"],as_index=False).size().reset_index()
    if 0 in country_item_scope_agg.columns.to_list():
        country_item_scope_agg.rename(columns={0:"size"}, inplace=True)
    country_item_scope_agg.sort_values("size", ascending=False, inplace=True)

    # May need to work out this section.
    country_item_scope_agg.rename(columns={"size":"Count"}, inplace=True)
    country_item_scope_agg = country_item_scope_agg.groupby(["Country","Scope"]).head(1)
    country_item_scope_agg["product-count"] = country_item_scope_agg["Items"] + " (" + country_item_scope_agg["Count"].astype(str) + ")"

    top_by_country_scope = country_item_scope_agg.pivot("Country","Scope","product-count")
    top_by_country_scope.reset_index(inplace=True)
    top_by_country_scope.fillna("",inplace=True)
    top_by_country_scope.to_csv(STATIC + "top_by_country_scope.csv",index=False)

    return "The products view data was processed!"

#----------------US Forecasting page processing-------------------------
def us_forecasting_process():
    # Get the first of each month from a given starting timestamp for the number in months.
    def month_accumulate(start_month, num_months):
        month_list = list()
        temp = start_month
        for i in range(0,num_months):
            next_month = temp + datetime.timedelta(days=32)
            day_subtract = next_month.day - 1
            next_month = next_month - datetime.timedelta(days=day_subtract)
            month_list.append(next_month)
            temp = next_month
        return month_list

    # Read in the saved model.
    us_forecast = joblib.load(STATIC_R + "us_certification_forecast_model.pkl")
    # Read in data calculated by US view.
    try:
        trend_df = pd.read_csv(STATIC_R + "us_trend_data.csv")
    except FileNotFoundError:
        return jsonify({"message": "ERROR: us_process must be run at least once before this process. Please POST to us_process"}), 400

    # Format and set index as datetime.
    trend_df["op_statusEffectiveDate"] = trend_df["op_statusEffectiveDate"].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))
    trend_df = trend_df.set_index("op_statusEffectiveDate")
    # Use trend data for time series forecasting.
    trend = trend_df.Trend

    # Remove the current month from the data, as the full count is not in place.
    c_y = str(datetime.datetime.now().year)
    c_m = str(datetime.datetime.now().month)
    c_start_m = c_y + "-" + c_m + "-01"
    current = datetime.datetime.strptime(c_start_m, "%Y-%m-%d")

    trend = trend.loc[trend.index < current]

    # Remove data from before the last date that the model was previously trained on.
    # Get a record of the last date used to train the model.
    with open(STATIC_R +"us_certification_forecast_model.json", 'r') as file:
        last_trained_date = json.load(file)

    last_trained_date = datetime.datetime.strptime(last_trained_date["date"], "%Y-%m-%d")


    # Walk forward validation procedure adapted from
    # https://machinelearningmastery.com/random-forest-for-time-series-forecasting/
    # Transform the trend data into a format for supervised learning.
    # Get the trends column and the shifted data column into a new dataframe. Extract values.
    trends = pd.DataFrame(trend)

    # Group by month.
    trends = trends.reset_index()
    trends["Month"] = trends.op_statusEffectiveDate.apply(lambda x: datetime.datetime.strftime(x, "%Y-%m"))
    trends = trends.groupby("Month", as_index=False)["Trend"].sum()
    trends["Year"] = trends["Month"].apply(lambda x: x.split("-")[0])
    trends["Month"] = trends["Month"].apply(lambda x: x.split("-")[1])

    trends["Shift_Back_1"] = trends["Trend"]
    trends.Shift_Back_1 = trends.Shift_Back_1.shift(1)
    trends["Shift_Back_2"] = trends.Shift_Back_1.shift(1)
    trends["Shift_Back_3"] = trends.Shift_Back_1.shift(2)

    trends["Date"] = trends["Year"] + "-" + trends["Month"] + "-01"

    # Reorganize the columns.
    trends = trends[["Year", "Month", "Shift_Back_3", "Shift_Back_2", "Shift_Back_1", "Trend", "Date"]]

    trends = trends.dropna()

    # If there is new data, retrain the model on all data.
    # This approach may be modified later.
    new_history = trend.loc[trend.index > last_trained_date]
    if len(new_history) > 0:
        # Save the previous model.
        model_name = "us_certification_forecast_model"
        model_extension = ".pkl"
        current = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H-%M-%S")
        joblib.dump(us_forecast, STATIC + model_name + " " + current + model_extension)

        trend_vals = trends.values
        hist_x = trend_vals[:, 3:-2]
        hist_y = trend_vals[:, -2]

        # Fit the data on the model.
        us_forecast.fit(hist_x, hist_y)

        joblib.dump(us_forecast, STATIC + model_name + model_extension)

        # For future predictions, get a record of the last date the model was trained on.
        #last_date = datetime.datetime.strftime((datetime.date.today() - datetime.timedelta(days=1)), "%Y-%m-%d")
        last_date = datetime.datetime.strftime(datetime.date.today(), "%Y-%m-%d")
        last_date = {"date": last_date}
        with open(STATIC +"us_certification_forecast_model.json", 'w') as file:
            json.dump(last_date, file)

        max_date = last_date

    else:
        # Get last date from file.
        with open(STATIC_R +"us_certification_forecast_model.json", 'r') as file:
                max_date = json.load(file)


    # Get the last month in the series.
    pred_month = max_date["date"]
    pred_month_dt = datetime.datetime.strptime(pred_month, "%Y-%m-%d")

    pred_month_start = str(pred_month_dt.year) + "-" + str(pred_month_dt.month) + "-" + "01"

    # check if there is any data for the current month.
    if len(trends.loc[trends["Date"] == pred_month_start]) == 0:
        pred_month_dt = pred_month_dt - datetime.timedelta(days=31)
        pred_month_start = str(pred_month_dt.year) + "-" + str(pred_month_dt.month) + "-" + "01"

    upcoming_months = month_accumulate(pred_month_dt, 6)

    # Get the last value in the dataset.
    last_month = trends.loc[trends["Date"] ==  max(trends["Date"])].values[0]

    # Predict for the next months.
    predictions = list()
    for pred_date in upcoming_months:
        # Copy the last month to be predicted.
        pred_month = last_month

        pred_month[0] = int(pred_date.year)
        pred_month[1] = int(pred_date.month)
        pred_month[2] = last_month[3] # Assign last month's shift back 2 to 3.
        pred_month[3] = last_month[4] # Assign last month's shift back 1 to 2.
        pred_month[4] = last_month[5] # Assign last month's value(trend) to shift back 1.
        pred_month[6] = pred_date

        # As in the notebook used to develop this model, not all of the features are used.
        temp_val =  us_forecast.predict(pred_month[3:-2].reshape(1, -1))[0]

        pred_month[5] = temp_val

        last_month = pred_month
        predictions.append(pred_month.copy())

    # Fix date column.
    trends["Date"] = trends["Date"].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))

    # Combine the pred_results of the prediction with the most recent past trend records.
    # Plot the result.
    pred_results = pd.DataFrame(predictions, columns = trends.columns)
    pred_results["Type"] = "Predicted"
    trends["Type"] = "Actual"
    trend_pred_df = pd.concat([trends, pred_results])
    trend_pred_df = trend_pred_df.reset_index()
    # Get about 6 months before the current month
    trend_pred_df = trend_pred_df.loc[trend_pred_df["Date"] > (pred_month_dt - datetime.timedelta(days=183))]
    # Reset month column.
    trend_pred_df = trend_pred_df.sort_values("Date")

    # Duplicate the last record of known value in order to show a smooth continuation.
    max_actual = trend_pred_df.loc[trend_pred_df["Type"]=="Actual","Date"].max()
    line_continue = trend_pred_df.loc[trend_pred_df["Date"]==max_actual].copy()
    line_continue["Type"] = "Predicted"
    trend_pred_show = pd.concat([trend_pred_df,line_continue]).reset_index()
    trend_pred_show.sort_values("Date", inplace=True)

    # sns.set_style('whitegrid')
    # sns.set_palette('dark')
    # sns.set_context("poster")

    # #sns.lineplot(data=trend, x="Month", y="Trend", hue="Type")
    # sns.relplot(data=trend_pred_show, x='Date', y='Trend', kind='line', hue='Type',height=10, aspect=1.5)
    # #plt.title('Certification Changes Over Time')
    # plt.xlabel('Date')
    # plt.ylabel('Monthly Change In Certification')
    # plt.xticks(rotation=30)
    # plt.savefig(STATIC_IMG + "US_forecast_month_change.png", bbox_inches="tight", pad_inches=0.3)

    fig = px.line(trend_pred_show,
        x="Date",
        y="Trend",
        markers=True,
        color="Type")

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    us_forecast_month_change_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "us_forecast_month_change.json", "w") as j:
        j.write(us_forecast_month_change_json)

    # Calculate the total count of overall operations throughout the timeframe of the prediction.
    start_count = trend_df.loc[trend_pred_df.Date.min(), "total_count"]

    first=True
    count_list = list()
    month_list = list()
    for index, row in trend_pred_df.iterrows():
        if first:
            current_count = start_count
            first=False
        else:
            current_count = current_count + row["Trend"]
        month_list.append(row["Date"])
        count_list.append(current_count)
    count_df = pd.DataFrame(zip(month_list, count_list), columns=["Date", "total_count"])

    trend_pred_count_df = trend_pred_df.merge(right=count_df,on="Date",how="inner")

    # Duplicate the last record of known value in order to show a smooth continuation.
    max_actual = trend_pred_count_df.loc[trend_pred_count_df["Type"]=="Actual","Date"].max()

    line_continue = trend_pred_count_df.loc[trend_pred_count_df["Date"]==max_actual].copy()
    line_continue["Type"] = "Predicted"

    trend_pred_count_show = pd.concat([trend_pred_count_df,line_continue]).reset_index()

    # sns.relplot(data=trend_pred_count_show, x='Date', y='total_count', kind='line', hue='Type',height=10, aspect=1.5)
    # #plt.title('Certification Changes Over Time')
    # plt.xlabel('Date')
    # plt.ylabel('Number of Certified Operations')
    # plt.xticks(rotation=30)
    # plt.savefig(STATIC_IMG + "US_forecast_total_count.png", bbox_inches="tight", pad_inches=0.3)
    trend_pred_count_show.sort_values("Date", inplace=True)
    fig = px.line(trend_pred_count_show,
        x="Date",
        y="total_count",
        markers=True,
        color="Type",
        labels={"total_count":"Number of Certified Operations"})

    fig.update_xaxes(tickformat = "%b %Y", tickangle=45, nticks=10)
    fig.update_traces(hovertemplate="%{y}")
    fig.update_layout(hovermode="x unified")

    us_forecast_count_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    with open(STATIC + "us_forecast_count.json", "w") as j:
        j.write(us_forecast_count_json)

    return "The US forecasting view data was processed!"