-- Core extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist during development cycles
DROP TABLE IF EXISTS components CASCADE;

-- The Master Core Hardware Component Table
CREATE TABLE components (
    part_id VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,                   -- mcu, sensor, power, level_shifter
    manufacturer_part_number VARCHAR(100),
    vcc_min_v NUMERIC(4,2) NOT NULL,
    vcc_max_v NUMERIC(4,2) NOT NULL,
    typical_current_ma NUMERIC(8,2) DEFAULT 0.0,
    logic_level_v NUMERIC(4,2) NOT NULL,             -- 3.3 or 5.0
    kicad_symbol VARCHAR(150) NOT NULL,
    kicad_footprint VARCHAR(150) NOT NULL,
    interfaces JSONB NOT NULL,                       -- Houses hardware mapping definitions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexing properties for rapid compiler search operations
CREATE INDEX idx_components_category ON components(category);
CREATE INDEX idx_components_interfaces ON components USING gin (interfaces);