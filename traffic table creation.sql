DROP DATABASE IF EXISTS traffic_violations;
CREATE DATABASE traffic_violations;
USE traffic_violations;

-- ==========================
-- STOPS  (one row per SeqID — the stop-level dimension)
-- ==========================
CREATE TABLE stops (
    seqid VARCHAR(50) PRIMARY KEY,

    date_of_stop DATE,
    time_of_stop TIME,
    stop_datetime DATETIME,

    location VARCHAR(255),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),

    geo_latitude DECIMAL(10,6),
    geo_longitude DECIMAL(10,6),

    state CHAR(2),

    INDEX idx_stop_date (date_of_stop),
    INDEX idx_stop_datetime (stop_datetime),
    INDEX idx_location (location(100)),
    INDEX idx_coordinates (latitude, longitude)
);

-- ==========================
-- VIOLATIONS  (many rows per SeqID — one row per charge)
-- ==========================
CREATE TABLE violations (
    violation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50) NOT NULL,

    violation_type VARCHAR(50),      -- Citation / Warning / ESERO / SERO
    charge VARCHAR(50),
    description TEXT,
    article VARCHAR(100),
    violation_category VARCHAR(50),  -- SPEEDING / LICENSE / REGISTRATION / INSURANCE / OTHER

    accident BOOLEAN DEFAULT FALSE,
    belts BOOLEAN DEFAULT FALSE,
    personal_injury BOOLEAN DEFAULT FALSE,
    property_damage BOOLEAN DEFAULT FALSE,
    fatal BOOLEAN DEFAULT FALSE,
    commercial_license BOOLEAN DEFAULT FALSE,
    hazmat BOOLEAN DEFAULT FALSE,
    commercial_vehicle BOOLEAN DEFAULT FALSE,
    alcohol BOOLEAN DEFAULT FALSE,
    contributed_to_accident BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (seqid) REFERENCES stops(seqid) ON DELETE CASCADE, -- deleting the parent automatically deletes the related child records.

    INDEX idx_violations_seqid (seqid),
    INDEX idx_charge (charge),
    INDEX idx_violation_type (violation_type),
    INDEX idx_violation_category (violation_category)
);

-- ==========================
-- DRIVER  (one row per SeqID)
-- ==========================
CREATE TABLE driver (
    seqid VARCHAR(50) PRIMARY KEY,

    race VARCHAR(50),
    gender CHAR(1),
    driver_city VARCHAR(100),
    driver_state VARCHAR(5),
    dl_state VARCHAR(5),

    FOREIGN KEY (seqid) REFERENCES stops(seqid) ON DELETE CASCADE,

    INDEX idx_driver_race (race),
    INDEX idx_driver_gender (gender)
);

DESCRIBE driver;

-- ==========================
-- VEHICLE  (one row per SeqID)
-- ==========================
CREATE TABLE vehicle (
    seqid VARCHAR(50) PRIMARY KEY,

    vehicle_type VARCHAR(100),
    vehicle_code VARCHAR(10),
    vehicle_category VARCHAR(100),
    make VARCHAR(100),
    model VARCHAR(100),
    year SMALLINT,
    color VARCHAR(50),

    FOREIGN KEY (seqid) REFERENCES stops(seqid) ON DELETE CASCADE,

    INDEX idx_make (make),
    INDEX idx_model (model),
    INDEX idx_vehicle_type (vehicle_type)
);

-- ==========================
-- SEARCH INFO  (one row per SeqID)
-- ==========================
CREATE TABLE search_info (
    seqid VARCHAR(50) PRIMARY KEY,

    search_conducted BOOLEAN,
    search_type VARCHAR(100),
    search_reason VARCHAR(255),
    search_outcome VARCHAR(255),
    search_disposition VARCHAR(255),
    search_arrest_reason VARCHAR(255),
    search_reason_for_stop VARCHAR(255),

    FOREIGN KEY (seqid) REFERENCES stops(seqid) ON DELETE CASCADE,

    INDEX idx_search_conducted (search_conducted)
);

-- ==========================
-- ENFORCEMENT  (one row per SeqID)
-- ==========================
CREATE TABLE enforcement (
    seqid VARCHAR(50) PRIMARY KEY,

    agency VARCHAR(50),
    subagency VARCHAR(100),
    district VARCHAR(10),
    arrest_type VARCHAR(100),
    arrest_code VARCHAR(5),
    arrest_description VARCHAR(255),
    work_zone BOOLEAN,

    FOREIGN KEY (seqid) REFERENCES stops(seqid) ON DELETE CASCADE,

    INDEX idx_agency (agency),
    INDEX idx_subagency (subagency)
);