import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
import os
from dotenv import load_dotenv

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "traffic_violations.env")
load_dotenv(dotenv_path=ENV_PATH)

st.set_page_config(page_title="Traffic Violations Dashboard", layout="wide")
st.title("🚦 Traffic Violations Insight System")

# DB CONNECTION

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
# Streamlit decorator
@st.cache_data
def run_query(query, params=None):
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df

# DATA PREPROCESSING

def preprocess(df):

    # REMOVE DUPLICATES
    df = df.drop_duplicates()

    # DATETIME CLEANING
    df['Date Of Stop'] = pd.to_datetime(df['Date Of Stop'], errors='coerce')
    df['Time Of Stop'] = df['Time Of Stop'].astype(str).str.replace('.', ':')
    df['Time Of Stop'] = pd.to_datetime(df['Time Of Stop'], errors='coerce').dt.time

    df['datetime'] = pd.to_datetime(
        df['Date Of Stop'].astype(str) + ' ' + df['Time Of Stop'].astype(str),
        errors='coerce'
    )

    # Time Feature Engineering
    df['hour'] = df['datetime'].dt.hour # Extracts hour
    df['time_bucket'] = pd.cut(
        df['hour'],
        bins=[0,6,12,18,24],
        labels=['Night','Morning','Afternoon','Evening']
    )

    # CLEAN LAT/LONG
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df.loc[df['Latitude'] == 0, 'Latitude'] = np.nan
    df.loc[df['Longitude'] == 0, 'Longitude'] = np.nan

    # BOOLEAN CLEANING
    bool_cols = ['Accident','Alcohol','Belts','Fatal','Personal Injury','Property Damage']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({
                'yes':1,'no':0,'true':1,'false':0
            })

    # CATEGORICAL CLEANING (uppercase)
    df['Race'] = df['Race'].str.upper()
    df['Gender'] = df['Gender'].str.upper().fillna('UNKNOWN')
    df['Color'] = df['Color'].str.upper()
    df['Make'] = df['Make'].str.upper()

    # VEHICLE YEAR
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df[(df['Year'] > 1960) & (df['Year'] < 2025)]

    return df

#  LOAD DATA

@st.cache_data
def load_data(path, limit=2000):
    df = pd.read_csv(path, nrows=limit)
    df = preprocess(df)
    return df

# Replace with your dataset path
DATA_PATH = "Traffic_Violations.csv"

# Row limit control (can be increased later)
ROW_LIMIT = 2000

try:
    df = load_data(DATA_PATH, limit=ROW_LIMIT)
except:
    st.error("Dataset not found. Place Traffic_Violations.csv in project folder.")
    st.stop()

# SIDEBAR FILTERS
st.sidebar.header("Filters")
# Creates dropdowns
vehicle_filter = st.sidebar.selectbox("Vehicle Type", ["All"] + list(df['VehicleType'].dropna().unique()))
race_filter = st.sidebar.selectbox("Race", ["All"] + list(df['Race'].dropna().unique()))
gender_filter = st.sidebar.selectbox("Gender", ["All"] + list(df['Gender'].dropna().unique()))

# APPLY FILTER
filtered_df = df.copy()
# Conditional Filtering
if vehicle_filter != "All":
    filtered_df = filtered_df[filtered_df['VehicleType'] == vehicle_filter]

if race_filter != "All":
    filtered_df = filtered_df[filtered_df['Race'] == race_filter]

if gender_filter != "All":
    filtered_df = filtered_df[filtered_df['Gender'] == gender_filter]

#  KPI
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Violations", len(filtered_df))
col2.metric("Accidents", int(filtered_df['Accident'].sum(skipna=True)))
col3.metric("Unique Locations", filtered_df['Location'].nunique())
col4.metric("Top Vehicle", filtered_df['Make'].mode()[0] if not filtered_df.empty else "N/A")

# NAVIGATION
page = st.sidebar.radio("Navigation", [
    "Overview",
    "Time Analysis",
    "Location Analysis",
    "Demographics",
    "Vehicle Analysis",
    "Accident Insights"
])

# OVERVIEW
if page == "Overview":
    st.header("Violation Overview")

    top_violations = filtered_df['Description'].value_counts().head(10)
    st.bar_chart(top_violations)

# TIME
elif page == "Time Analysis":
    st.header("Time Analysis")

    hourly = filtered_df['hour'].value_counts().sort_index()
    st.line_chart(hourly)

    bucket = filtered_df['time_bucket'].value_counts()
    st.bar_chart(bucket)

#  LOCATION
elif page == "Location Analysis":
    st.header("Location Analysis")

    top_locations = filtered_df['Location'].value_counts().head(10)
    st.bar_chart(top_locations)

#  DEMOGRAPHICS
elif page == "Demographics":
    st.header("Demographics")

    race_dist = filtered_df['Race'].value_counts()
    gender_dist = filtered_df['Gender'].value_counts()

    st.bar_chart(race_dist)
    st.bar_chart(gender_dist)

#  VEHICLE
elif page == "Vehicle Analysis":
    st.header("Vehicle Analysis")

    make_dist = filtered_df['Make'].value_counts().head(10)
    st.bar_chart(make_dist)

# ACCIDENT
elif page == "Accident Insights":
    st.header("Accident Insights")

    accident = filtered_df['Accident'].value_counts()
    st.bar_chart(accident)

    if 'Alcohol' in filtered_df.columns:
        alcohol = filtered_df['Alcohol'].value_counts()
        st.bar_chart(alcohol)


