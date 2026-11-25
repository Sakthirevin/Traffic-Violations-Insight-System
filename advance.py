"""Traffic Violations Insight System – EDA and Streamlit Dashboard."""

import os
import pandas as pd
import plotly.express as px
import streamlit as st
import pydeck as pdk

from traffic_data_cleaning import clean_traffic_data


# 1. PAGE AND DATA CONFIGURATION
st.set_page_config(
    page_title="Traffic Violations Insight System",
    page_icon="🚦",
    layout="wide"
)

DATA_PATH = os.getenv("TRAFFIC_DATA_FILE", "Traffic_Violations.csv")
SAMPLE_SIZE = int(os.getenv("DASHBOARD_SAMPLE_SIZE", "100000"))


# 2. LOAD AND PREPARE DATA
@st.cache_data(show_spinner="Loading and cleaning traffic data...")
def load_data(path, sample_size):
    df = pd.read_csv(path, low_memory=False)

    if sample_size > 0 and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    df = clean_traffic_data(df)

    # Prepare date and time fields for EDA.
    if "date_of_stop" in df:
        df["date_of_stop"] = pd.to_datetime(
            df["date_of_stop"], errors="coerce"
        )

    if "stop_datetime" in df:
        df["stop_datetime"] = pd.to_datetime(
            df["stop_datetime"], errors="coerce"
        )
    elif {"date_of_stop", "time_of_stop"}.issubset(df.columns):
        df["stop_datetime"] = pd.to_datetime(
            df["date_of_stop"].astype("string") + " " +
            df["time_of_stop"].astype("string"),
            errors="coerce"
        )

    if "stop_datetime" in df:
        df["hour"] = df["stop_datetime"].dt.hour
        df["weekday"] = df["stop_datetime"].dt.day_name()
        df["month"] = df["stop_datetime"].dt.month_name()

    # Use the real violation category when available.
    # Otherwise use violation_type; do not confuse it with vehicle_category.
    if "violation_category" not in df and "violation_type" in df:
        df["violation_category"] = df["violation_type"]

    return df


# 3. SIDEBAR FILTERS
def sidebar_filters(df):
    st.sidebar.header("Dashboard Filters")

    def options(column):
        if column not in df:
            return ["All"]
        values = df[column].dropna().astype(str).unique().tolist()
        return ["All"] + sorted(values)

    location = st.sidebar.selectbox("Location", options("location"))
    vehicle = st.sidebar.selectbox(
        "Vehicle Type", options("vehicle_category")
        if "vehicle_category" in df else options("vehicletype")
    )
    gender = st.sidebar.selectbox("Gender", options("gender"))
    race = st.sidebar.selectbox("Race", options("race"))
    category = st.sidebar.selectbox(
        "Violation Category / Type", options("violation_category")
    )

    if "date_of_stop" in df and df["date_of_stop"].notna().any():
        min_date = df["date_of_stop"].min().date()
        max_date = df["date_of_stop"].max().date()
        date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = ()

    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Violation Analysis", "Time Analysis",
         "Hotspots & Patrol", "Safety & Demographics"]
    )

    return {
        "location": location, "vehicle": vehicle, "gender": gender,
        "race": race, "category": category, "date_range": date_range,
        "page": page
    }


# 4. APPLY FILTERS
def filter_data(df, filters):
    result = df.copy()

    filter_columns = {
        "location": "location",
        "gender": "gender",
        "race": "race",
        "category": "violation_category"
    }

    vehicle_column = (
        "vehicle_category" if "vehicle_category" in result
        else "vehicletype"
    )
    filter_columns["vehicle"] = vehicle_column

    for key, column in filter_columns.items():
        value = filters[key]
        if value != "All" and column in result:
            result = result[result[column].astype(str) == value]

    dates = filters["date_range"]
    if len(dates) == 2 and "date_of_stop" in result:
        start, end = pd.to_datetime(dates[0]), pd.to_datetime(dates[1])
        result = result[result["date_of_stop"].between(start, end)]

    return result


# 5. COMMON KPI METRICS
def show_metrics(df):
    unique_stops = (
        df["seqid"].nunique() if "seqid" in df else len(df)
    )
    accidents = (
        int(df["accident"].fillna(False).astype(bool).sum())
        if "accident" in df else 0
    )
    injuries = (
        int(df["personal_injury"].fillna(False).astype(bool).sum())
        if "personal_injury" in df else 0
    )
    fatal = (
        int(df["fatal"].fillna(False).astype(bool).sum())
        if "fatal" in df else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Violation Records", f"{len(df):,}")
    c2.metric("Unique Stops", f"{unique_stops:,}")
    c3.metric("Accident Records", f"{accidents:,}")
    c4.metric("Injury / Fatal Records", f"{injuries:,} / {fatal:,}")


# 6. OVERVIEW – BUSINESS SUMMARY
def overview(df):
    st.subheader("Traffic Safety Overview")
    show_metrics(df)

    left, right = st.columns(2)

    with left:
        st.markdown("**Most Common Violations**")
        if "description" in df:
            top = df["description"].value_counts().head(10).reset_index()
            top.columns = ["Violation", "Records"]
            st.plotly_chart(
                px.bar(top, x="Records", y="Violation", orientation="h",
                       title="Top 10 Violations"),
                use_container_width=True
            )

    with right:
        st.markdown("**Most Frequently Cited Vehicle Makes**")
        if "make" in df:
            makes = df["make"].value_counts().head(10).reset_index()
            makes.columns = ["Vehicle Make", "Records"]
            st.plotly_chart(
                px.bar(makes, x="Vehicle Make", y="Records",
                       title="Top Vehicle Makes"),
                use_container_width=True
            )

    st.markdown("**Business use cases**")
    st.write(
        "- Use common violation patterns to plan road-safety education.\n"
        "- Use location and accident patterns to identify areas for safety review.\n"
        "- Use peak hours and busy locations to support patrol scheduling.\n"
        "- Use accident, injury and fatality records to inform safety policies."
    )


# 7. VIOLATION ANALYSIS
def violation_analysis(df):
    st.subheader("Violation Analysis")

    column = (
        "violation_category" if "violation_category" in df
        else "description"
    )
    counts = df[column].value_counts().head(15).reset_index()
    counts.columns = ["Violation", "Records"]

    st.plotly_chart(
        px.bar(counts, x="Records", y="Violation", orientation="h",
               title="Most Common Violation Categories / Types"),
        use_container_width=True
    )

    if "violation_type" in df:
        types = df["violation_type"].value_counts().reset_index()
        types.columns = ["Violation Type", "Records"]
        st.plotly_chart(
            px.pie(types, names="Violation Type", values="Records",
                   title="Violation Type Distribution", hole=0.35),
            use_container_width=True
        )


# 8. TIME ANALYSIS
def time_analysis(df):
    st.subheader("Violation Trends Over Time")

    if "stop_datetime" not in df or df["stop_datetime"].notna().sum() == 0:
        st.info("Date/time values are unavailable for time analysis.")
        return

    timed = df.dropna(subset=["stop_datetime"]).copy()
    timed["Hour"] = timed["stop_datetime"].dt.hour
    timed["Weekday"] = timed["stop_datetime"].dt.day_name()
    timed["Month"] = timed["stop_datetime"].dt.to_period("M").astype(str)

    left, right = st.columns(2)

    with left:
        hourly = timed.groupby("Hour").size().reset_index(name="Records")
        st.plotly_chart(
            px.line(hourly, x="Hour", y="Records", markers=True,
                    title="Violations by Hour"),
            use_container_width=True
        )

    with right:
        weekday_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        weekday = timed["Weekday"].value_counts().reindex(
            weekday_order, fill_value=0
        ).rename_axis("Weekday").reset_index(name="Records")
        st.plotly_chart(
            px.bar(weekday, x="Weekday", y="Records",
                   title="Violations by Weekday"),
            use_container_width=True
        )

    monthly = timed.groupby("Month").size().reset_index(name="Records")
    st.plotly_chart(
        px.line(monthly, x="Month", y="Records", markers=True,
                title="Monthly Violation Trend"),
        use_container_width=True
    )


# 9. GEOGRAPHIC HOTSPOTS AND PATROL PLANNING
def hotspot_analysis(df):
    st.subheader("Geographic Hotspots")

    # Geographic Map
    if {"latitude", "longitude"}.issubset(df.columns):

        geo = df[["latitude", "longitude"]].copy()

        # Convert coordinates to numeric
        geo["latitude"] = pd.to_numeric(
            geo["latitude"], errors="coerce"
        )
        geo["longitude"] = pd.to_numeric(
            geo["longitude"], errors="coerce"
        )

        # Remove missing coordinates
        geo = geo.dropna(subset=["latitude", "longitude"])

        # Convert NumPy data types to standard Python floats
        geo["latitude"] = geo["latitude"].astype("float64")
        geo["longitude"] = geo["longitude"].astype("float64")

        # Validate coordinate ranges
        geo = geo[
            geo["latitude"].between(-90, 90) &
            geo["longitude"].between(-180, 180)
        ]

        if not geo.empty:

            # Create map layer
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=geo,
                get_position="[longitude, latitude]",
                get_radius=100,
                get_fill_color=[220, 50, 70, 180],
                pickable=True,
            )

            # Set map center
            view_state = pdk.ViewState(
                latitude=float(geo["latitude"].mean()),
                longitude=float(geo["longitude"].mean()),
                zoom=10,
                pitch=0,
            )

            # Create map
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                tooltip={
                    "text": "Latitude: {latitude}\nLongitude: {longitude}"
                },
            )

            # Display map
            st.pydeck_chart(deck, use_container_width=True)

        else:
            st.info("No valid coordinates are available.")

    else:
        st.info("Latitude and longitude columns are unavailable.")

    # Top 15 Locations
    if "location" in df.columns:
        locations = df["location"].value_counts().head(15)

        st.plotly_chart(
            px.bar(
                locations.rename_axis("Location").reset_index(name="Records"),
                x="Records",
                y="Location",
                orientation="h",
                title="Top 15 Locations by Violation Volume"
            ),
            use_container_width=True
        )

    # Accident Risk Analysis
    if {"location", "accident"}.issubset(df.columns):

        risk = df.groupby("location").agg(
            Records=("accident", "size"),
            Accidents=("accident", lambda x: x.fillna(False).astype(bool).sum())
        ).reset_index()

        risk = risk[risk["Records"] >= 5].copy()

        risk["Accident Rate (%)"] = (
            risk["Accidents"] / risk["Records"] * 100
        ).round(1)

        risk = risk.sort_values(
            ["Accident Rate (%)", "Records"],
            ascending=False
        ).head(15)

        st.markdown("**Locations with elevated accident rates**")
        st.dataframe(risk, use_container_width=True)

    # Safety Insight
    st.caption(
        "Use hotspot volume and accident patterns as indicators for further "
        "road-safety review and patrol planning. High violation volume alone "
        "does not prove that a location has a high accident risk."
    )


# 10. SAFETY AND DEMOGRAPHIC ANALYSIS
def safety_demographics(df):
    st.subheader("Accidents, Injuries and Vehicle Damage")

    safety_columns = [
        c for c in ["accident", "personal_injury", "property_damage", "fatal"]
        if c in df
    ]

    if safety_columns:
        safety = pd.DataFrame({
            "Safety Indicator": safety_columns,
            "Records": [
                int(df[c].fillna(False).astype(bool).sum())
                for c in safety_columns
            ]
        })
        st.plotly_chart(
            px.bar(safety, x="Safety Indicator", y="Records",
                   title="Safety-Related Records"),
            use_container_width=True
        )

    left, right = st.columns(2)

    with left:
        if "gender" in df:
            gender = df["gender"].value_counts().reset_index()
            gender.columns = ["Gender", "Records"]
            st.plotly_chart(
                px.bar(gender, x="Gender", y="Records",
                       title="Violations by Gender"),
                use_container_width=True
            )

    with right:
        if "race" in df:
            race = df["race"].value_counts().head(10).reset_index()
            race.columns = ["Race", "Records"]
            st.plotly_chart(
                px.bar(race, x="Race", y="Records",
                       title="Violations by Recorded Race"),
                use_container_width=True
            )

    if {"race", "violation_category"}.issubset(df.columns):
        st.markdown("**Recorded Race vs Violation Category**")
        comparison = pd.crosstab(df["race"], df["violation_category"])
        st.dataframe(comparison, use_container_width=True)

    st.caption(
        "Demographic charts describe recorded enforcement data. They do not "
        "establish that demographic characteristics cause violations; "
        "interpret differences with care."
    )


# 11. RUN DASHBOARD
def main():
    st.title("🚦 Traffic Violations Insight System")
    st.write(
        "Explore violation patterns, road-safety indicators, time trends "
        "and geographic hotspots."
    )

    try:
        df = load_data(DATA_PATH, SAMPLE_SIZE)
    except FileNotFoundError:
        st.error(f"Dataset not found: {DATA_PATH}")
        st.stop()
    except Exception as error:
        st.error(f"Could not load or clean the dataset: {error}")
        st.stop()

    if df.empty:
        st.warning("The dataset contains no records.")
        st.stop()

    filters = sidebar_filters(df)
    filtered = filter_data(df, filters)

    if filtered.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    st.caption(f"Showing {len(filtered):,} of {len(df):,} records")
    st.divider()

    if filters["page"] == "Overview":
        overview(filtered)
    elif filters["page"] == "Violation Analysis":
        violation_analysis(filtered)
    elif filters["page"] == "Time Analysis":
        time_analysis(filtered)
    elif filters["page"] == "Hotspots & Patrol":
        hotspot_analysis(filtered)
    else:
        safety_demographics(filtered)


if __name__ == "__main__":
    main()
