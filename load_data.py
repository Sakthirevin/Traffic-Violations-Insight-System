import os
import pandas as pd
import mysql.connector
import traceback
from dotenv import load_dotenv

from traffic_data_cleaning import clean_traffic_data, data_quality_report

# 1. DATA CONFIGURATION

load_dotenv("traffic_violations.env")

DATA_FILE = os.getenv("TRAFFIC_DATA_FILE", "Traffic_Violations.csv")
ROW_LIMIT = int(os.getenv("ETL_ROW_LIMIT", "2000"))

# 2. MySQL TABLE CONFIGURATION
     # df -Complete cleaned data, df_unique - Duplicate-free cleaned data
TABLES = {

    "stops": {
    "source": "df_unique",
    "columns": ["seqid", "date_of_stop", "time_of_stop","location", "latitude", "longitude",
                "geo_latitude", "geo_longitude","state", "stop_datetime"],"duplicate_handling": True,},

    "violations": {
    "source": "df",
    "columns": ["seqid", "violation_type", "charge","description", "article","accident", "belts", "personal_injury",
                "property_damage", "fatal", "commercial_license","hazmat", "commercial_vehicle", "alcohol",
                "contributed_to_accident",],},

    "driver": {
        "source": "df_unique",
        "columns": ["seqid","race","gender","driver_city","driver_state","dl_state",],},

    "vehicle": {
        "source": "df_unique",
        "columns": ["seqid","vehicletype","vehicle_code","vehicle_category","make","model","year","color",],

        # Only needed because the DataFrame and MySQL names differ
        "db_columns": ["seqid","vehicle_type","vehicle_code","vehicle_category","make","model","year","color",],},

    "search_info": {
        "source": "df_unique",
        "columns": ["seqid","search_conducted","search_type","search_reason","search_outcome","search_disposition",
                    "search_arrest_reason","search_reason_for_stop",],},

    "enforcement": {
        "source": "df_unique",
        "columns": ["seqid","agency","subagency","district","arrest_type","arrest_code","arrest_description",
                    "work_zone",],},}

# 3. DATABASE CONNECTION
def connect_db():

   return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


# 4. Extract the CSV data
def load_data(file_name, limit):

    file_path = os.path.abspath(file_name)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    print("Reading dataset:", file_path)

    # Use Python parser for more robust CSV reading
    df = pd.read_csv(
        file_path,
        engine="python",
        encoding="utf-8-sig"
    )

    if 0 < limit < len(df):
        print(f"Sampling {limit:,} rows")
        df = df.sample(n=limit, random_state=42)

    return df.reset_index(drop=True)


# 5. Generate SQL Insert Query

def build_insert_query(table_name, columns, db_columns=None, duplicate_handling=False):
  # Default column mapping
    db_columns = db_columns or columns
  # Validate column count
    if len(columns) != len(db_columns):
        raise ValueError("Column count mismatch")
  # Generate placeholders
    placeholders = ", ".join(["%s"] * len(columns))
  # Generate final SQL query
    query = (
        f"INSERT INTO {table_name} "
        f"({', '.join(db_columns)}) "
        f"VALUES ({placeholders})"
    )
    if duplicate_handling:
       query += " ON DUPLICATE KEY UPDATE seqid = VALUES(seqid)"

    return query

# 6. Prepare SQL-Ready Rows
def build_rows(df, columns):
# Check missing columns
    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise KeyError(f"Missing required columns: {missing}")

# Select Required columns
    frame = df[columns].astype(object)

    # Handle missing values - Convert Pandas NaN/NaT to Python None → SQL NULL (MYSQL recognized)
    frame = frame.where(pd.notna(frame), None)
    # Convert DataFrame into tuples
    return list(frame.itertuples(index=False, name=None))

# 7. Load Data into MySQL Tables
def load_tables(conn, cursor, df, df_unique):
    # Mapping DataFrames - Creates a dict that connects the configuration names to actual df
    sources = {"df": df, "df_unique": df_unique}
    # Initialize
    results = {}

# Iterate through table configurations

    for table_name, config in TABLES.items():
  # Selecting correct df and extract required columns
        try:
            source_df = sources[config["source"]]
            columns = config["columns"]
  # Prepare SQL-ready rows - list of tuples.
            rows = build_rows(source_df, columns)
  # Generate SQL query
            query = build_insert_query(
                table_name, columns, config.get("db_columns"),config.get("duplicate_handling", False))
  # Perform bulk insertion
            if rows:
                cursor.executemany(query, rows)
                conn.commit()
  # Track insertion results
            results[table_name] = {
                "attempted": len(rows),
                "inserted": len(rows),
                "error": None
            }

            print(f"{table_name}: {len(rows):,} rows inserted")
   # Handle MySQL errors
        except mysql.connector.Error as err:
            conn.rollback() # reverses the uncommitted changes in the current transaction.

            results[table_name] = {
                "attempted": len(rows) if "rows" in locals() else 0,
                "inserted": 0,
                "error": str(err)
            }

            print(f"{table_name}: FAILED - {err}")

    return results

# 8. Main ETL Pipeline
def main():
# Initialize connection variables
    conn = None
    cursor = None

    try:
        # Connect to MySQL database
        conn = connect_db()
        cursor = conn.cursor()

        print("Dataset path:", repr(DATA_FILE))
        print("File exists:", os.path.isfile(DATA_FILE))

        # Extract data
        raw_df = load_data(DATA_FILE, ROW_LIMIT)
        print(f"Raw rows: {len(raw_df):,}")

        # Clean and preprocess data
        df = clean_traffic_data(raw_df)
        print(f"Cleaned rows: {len(df):,}")

        print("Raw violation_category:",
              "violation_category" in raw_df.columns)

        print("Cleaned violation_category:",
              "violation_category" in df.columns)

        print("Available columns:", df.columns.tolist())

        # Validate identifier
        if "seqid" not in df.columns:
            raise KeyError("Missing seqid column")

        # Remove duplicate stops
        df_unique = df.drop_duplicates(
            subset="seqid"
        ).reset_index(drop=True)

        # Load into MySQL
        results = load_tables(conn, cursor, df, df_unique)

        # Display insertion summary
        print("\nETL LOAD SUMMARY")

        for table, result in results.items():
            status = "SUCCESS" if result["error"] is None else "FAILED"

            print(
                f"{table}: {result['inserted']:,}/"
                f"{result['attempted']:,} rows - {status}"
            )

        # Display failed tables
        failed = [
            table for table, result in results.items()
            if result["error"]
        ]

        if failed:
            print("Failed tables:", ", ".join(failed))

        # Data quality report
        print("\nDATA QUALITY SUMMARY")

        for key, value in data_quality_report().items():
            print(f"{key}: {value}")

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        print(f"MySQL Error: {err}")

    except Exception as err:
     print(f"Error: {err}")
     traceback.print_exc()

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()

        print("Database connection closed.")


# 9. Program Entry Point
if __name__ == "__main__":
    main()