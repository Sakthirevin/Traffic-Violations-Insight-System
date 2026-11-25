# 🚦 Traffic Violations Insight System (TVIS)
### EDA | Data Cleaning & Preprocessing | ETL Pipeline | MySQL | Interactive Streamlit Dashboard

An end-to-end **Traffic Violations Insight System** designed to transform raw traffic violation records into meaningful insights through data cleaning, preprocessing, exploratory data analysis (EDA), SQL database integration, and interactive visualization.

The project focuses on identifying traffic violation patterns, analyzing road safety indicators, exploring geographical hotspots, and understanding violation trends across different time periods, locations, vehicle categories, and recorded driver demographics.

---

## 📌 Project Overview

Urban safety agencies generate large volumes of traffic violation records containing information about violations, vehicle details, driver demographics, geographical locations, and enforcement activities.

Raw datasets can contain missing and inconsistent values, duplicate traffic-stop records, invalid date and time formats, inconsistent categorical values, and incorrect geographical coordinates.

**TVIS addresses these challenges** through a structured data-processing and analytics workflow.

### 🎯 Project Objectives

- Clean and preprocess traffic violation datasets.
- Identify duplicate and inconsistent records.
- Standardize categorical, numerical, date, and time variables.
- Validate geographical coordinates and location information.
- Perform Exploratory Data Analysis to discover patterns.
- Design a normalized MySQL database with relational tables.
- Develop an interactive Streamlit dashboard.
- Examine traffic violation hotspots and road-safety indicators.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Manipulation | Pandas, NumPy |
| Database | MySQL |
| Database Integration | MySQL Connector |
| Data Visualization | Plotly |
| Interactive Dashboard | Streamlit |
| Geospatial Visualization | PyDeck |
| Environment Management | Python-dotenv |
| Data Processing | ETL, Data Cleaning, Preprocessing |
| Query Language | SQL |

---

## ⚙️ Project Architecture

The project follows a modular data analytics workflow.

```text
             RAW TRAFFIC DATASET
                      |
                      v
              DATA EXTRACTION
                      |
                      v
          DATA CLEANING & PREPROCESSING
                      |
                      v
             DATA QUALITY CHECKS
                      |
                      v
              DATA TRANSFORMATION
                      |
             +--------+---------+
             |                  |
             v                  v
       MYSQL DATABASE      CLEANED DATA
             |                  |
             v                  v
       NORMALIZED TABLES    EXPLORATORY DATA
             |              ANALYSIS (EDA)
             |                  |
             +--------+---------+
                      |
                      v
             STREAMLIT DASHBOARD
                      |
                      v
              INTERACTIVE INSIGHTS
```

---

## 🧹 1. Data Cleaning & Preprocessing

Implemented a dedicated preprocessing module using Pandas and NumPy.

### Data Cleaning Operations

- Standardized column names using lowercase formatting and underscores.
- Removed exact duplicate records.
- Identified repeated traffic-stop IDs (`seqid`).
- Converted date columns into datetime format.
- Standardized time values and created a combined `stop_datetime` column.
- Standardized categorical text values.
- Normalized gender values into M/F categories.
- Standardized vehicle manufacturers and colors.
- Extracted vehicle codes and vehicle categories using regular expressions.
- Extracted arrest codes, descriptions, and district information.
- Converted Yes/No values into Boolean values.
- Handled missing values and non-applicable search information.
- Validated latitude and longitude coordinates.
- Extracted geographical coordinates from geolocation fields.
- Identified coordinate mismatches.
- Validated state abbreviations and vehicle manufacturing years.
- Optimized numerical and categorical data types to reduce memory usage.

### Data Quality Monitoring

The preprocessing module maintains a data quality report containing:

- Input row count.
- Exact duplicates removed.
- Repeated sequence ID count.
- Invalid date count.
- Invalid latitude and longitude counts.
- Geolocation coordinate mismatches.
- Invalid vehicle manufacturing years.
- Missing Boolean values handled.
- Final output row and column counts.

---

## 🔄 2. ETL Pipeline – Python & MySQL

Developed a modular ETL pipeline to extract, transform, and load traffic violation data into a relational MySQL database.

### ETL Workflow

**Extract**
- Read traffic violation records from CSV files.
- Support configurable row sampling.
- Validate dataset availability.

**Transform**
- Execute the centralized data-cleaning module.
- Prepare duplicate-free stop-level records.
- Convert missing Pandas values into SQL-compatible NULL values.
- Prepare SQL-ready tuples.
- Validate required columns before insertion.

**Load**
- Dynamically generate SQL INSERT queries.
- Perform bulk insertion using `executemany()`.
- Implement duplicate-key handling for stop records.
- Manage database transactions using commit and rollback.
- Capture insertion errors and generate table-wise load summaries.

### MySQL Database Design

Designed a relational database named `traffic_violations` with six tables.

| Table | Purpose |
|---|---|
| `stops` | Traffic stop information, date, time, and geographical coordinates |
| `violations` | Violation types, charges, descriptions, and safety indicators |
| `driver` | Driver demographics and residential information |
| `vehicle` | Vehicle type, manufacturer, model, year, and color |
| `search_info` | Search-related information and outcomes |
| `enforcement` | Agency, subagency, district, and arrest information |

**Database Design Features**
- Primary key and foreign key relationships.
- One-to-one and one-to-many relational structures.
- Indexed columns for frequently queried fields.
- Cascading deletion for dependent records.
- Separation of stop-level and violation-level information.

---

## 📊 3. Exploratory Data Analysis (EDA)

Performed structured exploratory analysis to understand traffic violation patterns and road-safety indicators.

### Key Analysis Areas

**Violation Analysis**
- Most common violation categories.
- Violation type distribution.
- Frequently recorded violation descriptions.

**Time-Based Analysis**
- Violations by hour.
- Violations by weekday.
- Monthly violation trends.

**Geographical Analysis**
- Geographic traffic violation distribution.
- Top 15 locations by violation volume.
- Locations with elevated accident rates.
- Latitude and longitude-based hotspot visualization.

**Vehicle Analysis**
- Most frequently cited vehicle manufacturers.
- Vehicle category distribution.
- Vehicle-related violation patterns.

**Safety Analysis**
- Accident-related records.
- Personal injury records.
- Property damage records.
- Fatality-related records.

**Demographic Analysis**
- Violations by recorded gender.
- Violations by recorded race.
- Recorded demographics versus violation categories.

---

## 📈 4. Interactive Streamlit Dashboard

Developed an interactive dashboard using Streamlit, Plotly, and PyDeck.

### Dashboard Modules

**1. Overview**
- Total violation records.
- Unique traffic stops.
- Accident records.
- Injury and fatality records.
- Top 10 violation descriptions.
- Frequently cited vehicle manufacturers.

**2. Violation Analysis**
- Most common violation categories and types.
- Violation type distribution using interactive charts.

**3. Time Analysis**
- Hourly violation trends.
- Weekday violation patterns.
- Monthly violation trends.

**4. Hotspots & Patrol**
- Geographical traffic violation mapping.
- Top 15 locations by violation volume.
- Location-based accident rate analysis.

**5. Safety & Demographics**
- Accident and injury indicators.
- Property damage and fatality records.
- Gender-based analysis.
- Race-based analysis.
- Demographic versus violation category comparison.

### Interactive Filters

Users can filter dashboard records using:

- Location
- Vehicle Type
- Gender
- Race
- Violation Category / Type
- Date Range

The dashboard also uses Streamlit data caching to improve data-loading performance.

---

## 📂 Project Structure

```text
Traffic-Violations-Insight-System/
│
├── load_data.py
├── traffic_data_cleaning.py
├── advance.py
├── traffic_table_creation.sql
├── Traffic_Violations.csv
├── traffic_violations.env
├── requirements.txt
└── README.md
```

| File | Description |
|---|---|
| `load_data.py` | ETL pipeline and MySQL data loading |
| `traffic_data_cleaning.py` | Data cleaning, preprocessing, and quality monitoring |
| `advance.py` | EDA and interactive Streamlit dashboard |
| `traffic_table_creation.sql` | MySQL database and table creation |
| `Traffic_Violations.csv` | Raw traffic violation dataset |
| `traffic_violations.env` | Database and dataset configuration |
| `requirements.txt` | Project dependencies |
| `README.md` | Project documentation |

---

## 💡 Business Use Cases

This project demonstrates how traffic violation analytics can support:

- **Road Safety Management:** Understand accident and injury patterns.
- **Geographical Hotspot Identification:** Identify locations with high violation volumes.
- **Patrol Planning:** Support data-informed decisions regarding patrol deployment.
- **Traffic Policy Development:** Provide analytical information for road-safety planning.
- **Enforcement Analysis:** Understand violation and enforcement patterns.
- **Vehicle Analytics:** Identify frequently recorded vehicle categories and manufacturers.

*Note: High violation volume is an indicator for further investigation and does not independently establish accident risk.*

---

## 🎯 Key Learning Outcomes

Through this project, I gained practical experience in:

- End-to-end data analytics workflow development.
- Handling large and inconsistent datasets.
- Data cleaning and preprocessing with Pandas and NumPy.
- Exploratory Data Analysis and data interpretation.
- SQL database design and normalization.
- Python-based ETL pipeline development.
- Bulk data insertion and database transaction management.
- Interactive dashboard development using Streamlit.
- Data visualization using Plotly.
- Geospatial data validation and visualization using PyDeck.
- Data quality monitoring and error handling.
