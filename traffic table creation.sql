USE traffic_violations_db;
-- MAIN table → violations
CREATE TABLE violations (
    violation_id INT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50),
    date_of_stop DATE,
    time_of_stop TIME,
    location TEXT,
    latitude FLOAT,
    longitude FLOAT,
    violation_type VARCHAR(50),
    charge VARCHAR(50),
    accident BOOLEAN
);
-- Driver table
CREATE TABLE driver (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50),
    race VARCHAR(20),
    gender VARCHAR(10),
    driver_city VARCHAR(50),
    driver_state VARCHAR(20),
    dl_state VARCHAR(20)
);
-- Vehicle table
CREATE TABLE vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50),
    vehicle_type VARCHAR(50),
    make VARCHAR(50),
    model VARCHAR(50),
    year INT,
    color VARCHAR(20)
);
-- Search_info table
CREATE TABLE search_info (
    search_id INT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50),
    search_conducted BOOLEAN,
    search_type VARCHAR(50),
    search_reason VARCHAR(50),
    search_outcome VARCHAR(50),
    search_disposition VARCHAR(50)
);
-- Enforcement table
CREATE TABLE enforcement (
    enforcement_id INT AUTO_INCREMENT PRIMARY KEY,
    seqid VARCHAR(50),
    agency VARCHAR(50),
    subagency VARCHAR(100),
    arrest_type VARCHAR(50),
    work_zone BOOLEAN
);

SHOW TABLES;

-- Update violations table
ALTER TABLE violations
ADD description TEXT,
ADD article VARCHAR(50),
ADD belts BOOLEAN,
ADD personal_injury BOOLEAN,
ADD property_damage BOOLEAN,
ADD fatal BOOLEAN,
ADD commercial_license BOOLEAN,
ADD hazmat BOOLEAN,
ADD commercial_vehicle BOOLEAN,
ADD alcohol BOOLEAN,
ADD state VARCHAR(10);

-- Update search_info
ALTER TABLE search_info
ADD search_arrest_reason VARCHAR(50),
ADD search_reason_for_stop VARCHAR(50);

-- Add timestamp
ALTER TABLE violations
ADD stop_datetime DATETIME;

-- Add indexes
CREATE INDEX idx_seqid ON violations(seqid);
CREATE INDEX idx_date ON violations(date_of_stop);
CREATE INDEX idx_location ON violations(latitude, longitude);
CREATE INDEX idx_violation_type ON violations(violation_type);
