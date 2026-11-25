"""Traffic Violations Insight System - Data Cleaning & Preprocessing."""
# 1. Import required libraries
import numpy as np
import pandas as pd

# 2. Define constants and mapping dictionaries
# mappings help maintain consistency across the dataset.
# Boolean columns:
BOOL_COLS = [
    "accident", "belts", "personal_injury", "property_damage", "fatal",
    "commercial_license", "hazmat", "commercial_vehicle", "alcohol",
    "work_zone", "search_conducted", "contributed_to_accident",
]

# Boolean mapping:
BOOL_MAP = {
    "YES": True, "Y": True, "TRUE": True, "1": True,
    "NO": False, "N": False, "FALSE": False, "0": False,
}
NOT_APPLICABLE = [
    "search_type", "search_reason", "search_outcome", "search_disposition",
    "search_arrest_reason", "search_reason_for_stop",
]
STATE_COLS = ["state", "driver_state", "dl_state"]
MAKE_MAP = {"CHEV": "CHEVROLET", "TOYT": "TOYOTA", "MERZ": "MERCEDES", "HYUN": "HYUNDAI"}
COLOR_MAP = {"BLK": "BLACK", "WHI": "WHITE", "SIL": "SILVER", "BLU": "BLUE", "REDD": "RED"}

# 3. Data quality monitoring
"""This dictionary stores information about the cleaning process"""
_quality = {}

def data_quality_report():
    """function to return a copy of the data quality report - tracked metrics"""
    return _quality.copy()

# 4. Main cleaning function initialization
def clean_traffic_data(df):
    """Allows the function to update the quality dictionary."""
    global _quality
    _quality = {"input_rows": len(df)}

    df = df.copy()

  # Standardize column names:
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(r"\s+", "_", regex=True))
    before = len(df)
  # Remove exact duplicates:
    df = df.drop_duplicates(ignore_index=True)
    _quality["exact_duplicates_removed"] = before - len(df)

# Handle sequence IDs
    if "seqid" in df:
        df["seqid"] = df["seqid"].astype("string").str.strip()
# Counts repeated sequence IDs
        _quality["repeated_seqid_rows"] = int(
            df["seqid"].duplicated().sum())

# 2-3. Clean date/time and create a combined timestamp.
    if "date_of_stop" in df:
        old_valid = df["date_of_stop"].notna().sum()
        df["date_of_stop"] = pd.to_datetime(df["date_of_stop"], errors="coerce")
        future = df["date_of_stop"] > pd.Timestamp.now().normalize()
        df.loc[future, "date_of_stop"] = pd.NaT
        _quality["invalid_dates"] = int(old_valid - df["date_of_stop"].notna().sum())

    if "time_of_stop" in df:
        time_text = (df["time_of_stop"].astype("string").str.strip()
                     .str.replace(".", ":", regex=False))
        df["time_of_stop"] = pd.to_datetime(
            time_text, format="%H:%M:%S", errors="coerce"
        ).dt.time
# combine the date and time into a single timestamp column.
    if {"date_of_stop", "time_of_stop"}.issubset(df.columns):
        df["stop_datetime"] = pd.to_datetime(
            df["date_of_stop"].astype("string") + " " +
            df["time_of_stop"].astype("string"), errors="coerce"
        )

# 4-7, 30-35, 37-42. Standardize text and known category/code values.
    text_cols = df.select_dtypes(include=["object", "string"]).columns.difference(BOOL_COLS)
    df[text_cols] = df[text_cols].apply(
        lambda s: s.astype("string").str.strip().str.upper())
    df[text_cols] = df[text_cols].replace({"": pd.NA, "NAN": pd.NA, "NONE": pd.NA})

    if "gender" in df:
        df["gender"] = df["gender"].replace({"MALE": "M", "FEMALE": "F"})
        df["gender"] = df["gender"].where(df["gender"].isin(["M", "F"]), "UNKNOWN")

    if "make" in df:
        df["make"] = df["make"].replace(MAKE_MAP)
    if "color" in df:
        df["color"] = df["color"].replace(COLOR_MAP)
    if "location" in df:
        df["location"] = (df["location"].str.replace("@", "/", regex=False)
                          .str.replace(r"\s+", " ", regex=True))
# 5. Clean legal identifiers
    # Remove unwanted spaces
    for col in ["charge", "search_reason", "search_reason_for_stop", "search_arrest_reason"]:
        if col in df:
            df[col] = df[col].str.replace(" ", "", regex=False)

    # Vehicle type extraction
    for source in ["vehicletype", "vehicle_type"]:
        if source in df:
            df[["vehicle_code", "vehicle_category"]] = df[source].str.extract(
                r"(\d+)\s*-\s*(.*)")
            break
    # Arrest type extraction
    if "arrest_type" in df:
        df[["arrest_code", "arrest_description"]] = df["arrest_type"].str.extract(
            r"([A-Z])\s*-\s*(.*)")
    # District extraction
    if "subagency" in df:
        df["district"] = df["subagency"].str.extract(r"(\d+)")

# 8-9, 43. Geolocation and coordinate validation.
    #  validate the latitude and longitude values against their valid geographical ranges
    for col, low, high in [("latitude", -90, 90), ("longitude", -180, 180)]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            invalid = df[col].eq(0) | ~df[col].between(low, high)
            _quality[f"invalid_{col}"] = int(invalid.sum())
            df.loc[invalid, col] = np.nan
    # Extract geolocation coordinates
    if "geolocation" in df:
        geo = df["geolocation"].astype("string").str.extract(
            r"\(?\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\)?"
        ).apply(pd.to_numeric, errors="coerce")
        geo.columns = ["geo_latitude", "geo_longitude"]
        invalid_geo = (
            geo["geo_latitude"].eq(0) & geo["geo_longitude"].eq(0)
        ) | ~geo["geo_latitude"].between(-90, 90) | ~geo["geo_longitude"].between(-180, 180)
        geo.loc[invalid_geo, :] = np.nan
        df[geo.columns] = geo
    # Compare coordinate columns to identify mismatches.
        if {"latitude", "longitude"}.issubset(df.columns):
            both = df[["latitude", "longitude"]].notna().all(axis=1) & geo.notna().all(axis=1)
            mismatch = both & (
                (df["latitude"] - geo["geo_latitude"]).abs().gt(0.01) |
                (df["longitude"] - geo["geo_longitude"]).abs().gt(0.01)
            )
            _quality["geolocation_coordinate_mismatches"] = int(mismatch.sum())

# 27, 40-41. State abbreviation validation
    for col in STATE_COLS:
        if col in df:
            valid = df[col].astype("string").str.fullmatch(r"[A-Z]{2}", na=False)
            _quality[f"invalid_{col}"] = int((df[col].notna() & ~valid).sum())
            df.loc[~valid, col] = pd.NA

    # 29. Validate vehicle manufacture year.
    if "year" in df:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        invalid_year = ~df["year"].between(1960, pd.Timestamp.now().year)
        _quality["invalid_vehicle_years"] = int(invalid_year.sum())
        df.loc[invalid_year, "year"] = np.nan

    # 10-20, 36. Boolean normalization
    bool_cols = [c for c in BOOL_COLS if c in df]
    for col in bool_cols:
        df[col] = df[col].astype("string").str.strip().str.upper().map(BOOL_MAP)

    # 21-26. Handle search-related missing values
    if "search_conducted" in df:
        not_searched = df["search_conducted"].eq(False)
        for col in NOT_APPLICABLE:
            if col in df:
                df.loc[df[col].isna() & not_searched, col] = "NOT_APPLICABLE"

    # Handle missing values
    protected = {
        "race", "seqid", "latitude", "longitude", "geo_latitude", "geo_longitude",
        "date_of_stop", "time_of_stop", "stop_datetime", "timestamp", "year",
        *STATE_COLS,
    }
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if col not in protected and col not in BOOL_COLS:
            df[col] = df[col].fillna("UNKNOWN")

    # Boolean missing values
    for col in bool_cols:
        missing = int(df[col].isna().sum())
        if missing:
            _quality[f"{col}_missing_filled_false"] = missing
        df[col] = df[col].fillna(False).astype(bool)

    # Optimize memory usage
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

# Convert repeated text columns into category
    category_cols = [
        "agency", "subagency", "description", "gender", "state", "driver_state",
        "dl_state", "make", "model", "color", "violation_type", "vehicle_category",
        "race", "arrest_type",
    ]
    for col in category_cols:
        if col in df:
            df[col] = df[col].astype("category")
# Final data quality report
    _quality["output_rows"] = len(df)
    _quality["output_columns"] = len(df.columns)
    return df

# Main execution block
if __name__ == "__main__":
    data = pd.read_csv("Traffic_Violations.csv")
    cleaned_data = clean_traffic_data(data)
    cleaned_data.to_csv("cleaned_traffic_violations.csv", index=False)
    print("Original shape:", data.shape)
    print("Cleaned shape:", cleaned_data.shape)
    print("Data quality report:", data_quality_report())
