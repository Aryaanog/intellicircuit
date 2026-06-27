import psycopg2
import json
from decimal import Decimal

# Establish local database connection credentials
DB_PARAMS = {
    "dbname": "intellicircuit",
    "user": "postgres",
    "password": "aryaan",
    "host": "localhost",
    "port": 5432
}

def seed_database():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    components_to_seed = [
        # 1. THE MCU NODE: ESP32 DEVKIT V1
        (
            "mcu_esp32_devkit",
            "ESP32 NodeMCU Development Board",
            "mcu",
            "ESP32-32D",
            3.0, 3.6, 80.0, 3.3,
            "MCU_Espressif:ESP32-WROOM-32",
            "RF_Module:ESP32-WROOM-32E",
            json.dumps({
                "buses": {
                    "I2C_0": {"sda_pin": "GPIO21", "scl_pin": "GPIO22"},
                    "UART_0": {"tx_pin": "GPIO1", "rx_pin": "GPIO3"},
                    "SPI_0": {"mosi": "GPIO23", "miso": "GPIO19", "sclk": "GPIO18", "cs": "GPIO5"}
                },
                "gpio_pins": ["GPIO2", "GPIO4", "GPIO12", "GPIO13", "GPIO14", "GPIO15"],
                "adc_pins": ["GPIO32", "GPIO33", "GPIO34", "GPIO35"]
            })
        ),
        # 2. THE LOW-POWER I2C SENSOR: MPU6050
        (
            "sensor_mpu6050",
            "MPU-6050 6-Axis IMU Breakout",
            "sensor",
            "MPU-6050",
            3.0, 5.0, 4.0, 3.3,
            "Sensor_Motion:MPU-6050",
            "Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
            json.dumps({
                "protocol": "I2C",
                "pins": {
                    "VCC": "VCC",
                    "GND": "GND",
                    "SDA": "SDA",
                    "SCL": "SCL"
                },
                "address_default": "0x68"
            })
        ),
        # 3. THE 5V DIGITAL SENSOR: HC-SR04 (Triggers voltage violations on ESP32)
        (
            "sensor_hc_sr04",
            "HC-SR04 Ultrasonic Distance Sensor",
            "sensor",
            "HC-SR04",
            4.5, 5.5, 15.0, 5.0,
            "Sensor_Distance:HC-SR04",
            "Sensor_Distance:HC-SR04",
            json.dumps({
                "protocol": "DIGITAL_IO",
                "pins": {
                    "VCC": "VCC",
                    "GND": "GND",
                    "TRIG": "TRIG_PIN",
                    "ECHO": "ECHO_PIN"
                }
            })
        ),
        # 4. AUTO-INJECTABLE INFRASTRUCTURE: BSS138 4-CHANNEL LEVEL SHIFTER
        (
            "subcircuit_bss138_shifter",
            "BSS138 4-Channel Bi-Directional Logic Level Converter",
            "level_shifter",
            "BSS138_MODULE",
            2.7, 5.5, 0.1, 3.3,
            "Logic_Level:4-Channel-Shifter",
            "Logic_Level:4-Channel-Shifter-Module",
            json.dumps({
                "protocol": "TRANSLATOR",
                "low_side_ref": "LV",
                "high_side_ref": "HV",
                "channels": [
                    {"lv_pin": "LV1", "hv_pin": "HV1"},
                    {"lv_pin": "LV2", "hv_pin": "HV2"},
                    {"lv_pin": "LV3", "hv_pin": "HV3"},
                    {"lv_pin": "LV4", "hv_pin": "HV4"}
                ]
            })
        )
    ]

    insert_query = """
        INSERT INTO components (
            part_id, display_name, category, manufacturer_part_number,
            vcc_min_v, vcc_max_v, typical_current_ma, logic_level_v,
            kicad_symbol, kicad_footprint, interfaces
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (part_id) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            category = EXCLUDED.category,
            interfaces = EXCLUDED.interfaces;
    """

    for comp in components_to_seed:
        cur.execute(insert_query, comp)
        
    conn.commit()
    cur.close()
    conn.close()
    print("Successfully initialized and seeded Day 1 Hardware Registry.")

if __name__ == "__main__":
    seed_database()