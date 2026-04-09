import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

# CONFIG
load_dotenv("traffic_violations.env")
LIMIT = 2000

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

print("DB connected")

# LOAD LIMITED DATA
df = pd.read_csv("Traffic_Violations.csv", nrows=LIMIT)

# CLEANING Process
# Handle Missing Values
df = df.astype(object).where(pd.notnull(df), None)

# Boolean Cleaning Function
def clean_bool(x):
    return 1 if str(x).lower() in ["yes","y","true","1"] else 0

# Tuple Cleaning Function
def clean_tuple(row):
    return tuple(None if pd.isna(x) else x for x in row)

# FIX TIME FORMAT
df["Time Of Stop"] = df["Time Of Stop"].astype(str).str.replace(".", ":", regex=False)

# FIX DATE
df["Date Of Stop"] = pd.to_datetime(
    df["Date Of Stop"],
    format="%m/%d/%Y",
    errors="coerce" # Force conversion into null value
).dt.date # Date accessor

# FIX TIME
df["Time Of Stop"] = pd.to_datetime(
    df["Time Of Stop"],
    format="%H:%M:%S",
    errors="coerce"
).dt.time # Time accessor

# REMOVE INVALID ROWS (both date & time)
df = df.dropna(subset=["Date Of Stop"])

# BOOLEAN FIX
bool_cols = [
    "Accident","Belts","Personal Injury","Property Damage","Fatal",
    "Commercial License","HAZMAT","Commercial Vehicle","Alcohol",
    "Work Zone","Search Conducted"
]

for col in bool_cols:
    df[col] = df[col].apply(clean_bool)

# DATETIME
df["stop_datetime"] = pd.to_datetime(
    df["Date Of Stop"].astype(str) + " " + df["Time Of Stop"].astype(str),
    errors="coerce"
)

# INSERT - VIOLATIONS

violations_data = [
    clean_tuple(row)
    for row in df[[
        "SeqID","Date Of Stop","Time Of Stop","Location",
        "Latitude","Longitude","Violation Type","Charge",
        "Accident","Description","Article","Belts",
        "Personal Injury","Property Damage","Fatal",
        "Commercial License","HAZMAT","Commercial Vehicle",
        "Alcohol","State","stop_datetime"
    ]].to_numpy()
]

cursor.executemany("""
INSERT INTO violations (
seqid, date_of_stop, time_of_stop, location,
latitude, longitude, violation_type, charge,
accident, description, article, belts,
personal_injury, property_damage, fatal,
commercial_license, hazmat, commercial_vehicle,
alcohol, state, stop_datetime
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""", violations_data)

# REMOVE DUPLICATES
df_unique = df.drop_duplicates(subset=["SeqID"])

# DRIVER

driver_data = [
    clean_tuple(row)
    for row in df_unique[[
        "SeqID","Race","Gender",
        "Driver City","Driver State","DL State"
    ]].to_numpy()
]

cursor.executemany("""
INSERT INTO driver (
seqid, race, gender, driver_city, driver_state, dl_state
)
VALUES (%s,%s,%s,%s,%s,%s)
""", driver_data)

# VEHICLE

vehicle_data = [
    clean_tuple(row)
    for row in df_unique[[
        "SeqID","VehicleType","Make","Model","Year","Color"
    ]].to_numpy()
]

cursor.executemany("""
INSERT INTO vehicle (
seqid, vehicle_type, make, model, year, color
)
VALUES (%s,%s,%s,%s,%s,%s)
""", vehicle_data)

# SEARCH INFO

search_data = [
    clean_tuple(row)
    for row in df_unique[[
        "SeqID","Search Conducted","Search Type",
        "Search Reason","Search Outcome",
        "Search Disposition",
        "Search Arrest Reason",
        "Search Reason For Stop"
    ]].to_numpy()
]

cursor.executemany("""
INSERT INTO search_info (
seqid, search_conducted, search_type,
search_reason, search_outcome,
search_disposition, search_arrest_reason,
search_reason_for_stop
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""", search_data)

# ENFORCEMENT

enforcement_data = [
    clean_tuple(row)
    for row in df_unique[[
        "SeqID","Agency","SubAgency","Arrest Type","Work Zone"
    ]].to_numpy()
]

cursor.executemany("""
INSERT INTO enforcement (
seqid, agency, subagency, arrest_type, work_zone
)
VALUES (%s,%s,%s,%s,%s)
""", enforcement_data)

# FINAL COMMIT

conn.commit()

cursor.close()
conn.close()

print(f" SUCCESS: Inserted {LIMIT} rows without errors")