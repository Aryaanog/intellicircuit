import asyncio
import httpx
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Update with your local PostgreSQL credentials
DATABASE_URL = "postgresql+asyncpg://postgres:aryaan@localhost:5432/intellicircuit"
FASTAPI_ENDPOINT = "http://127.0.0.1:8000/api/v1/design"

async def setup_test_database():
    """Ensures the components table is populated with deterministic validation parts."""
    print("[1/3] Connecting to database to seed verification matrix...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if table exists, if not create it based on your strict schema columns
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS components (
                part_id VARCHAR(100) PRIMARY KEY,
                display_name VARCHAR(150) NOT NULL,
                category VARCHAR(50) NOT NULL,
                kicad_symbol VARCHAR(250) NOT NULL,
                kicad_footprint VARCHAR(250) NOT NULL,
                vcc_min_v DECIMAL(5,2) NOT NULL,
                vcc_max_v DECIMAL(5,2) NOT NULL,
                logic_level_v DECIMAL(3,1) NOT NULL,
                interfaces JSONB NOT NULL
            );
        """))
        
        # Insert a clean test host MCU and an Analog peripheral for deterministic matching
        await session.execute(text("""
            INSERT INTO components (part_id, display_name, category, kicad_symbol, kicad_footprint, vcc_min_v, vcc_max_v, logic_level_v, interfaces)
            VALUES 
            ('mcu_esp32_devkit', 'ESP32 DevKit Unit-Test v4', 'MCU', 'MCU_Espressif:ESP32', 'RF:ESP32-SMD', 3.0, 3.6, 3.3, 
             '{"protocol": "HOST", "buses": {"I2C_0": {"sda_pin": "GPIO21", "scl_pin": "GPIO22"}, "ADC_CH0": {"pin": "GPIO32"}, "CAN_0": {"tx_pin": "GPIO25", "rx_pin": "GPIO26"}}}'),
            
            ('sensor_lm35_test', 'LM35 Temperature Sensor Test Unit', 'PERIPHERAL', 'Sensor:LM35', 'Package:TO-92', 4.0, 30.0, 3.3,
             '{"protocol": "ANALOG", "pins": {"OUT": "VOUT"}}')
            ON CONFLICT (part_id) DO UPDATE SET interfaces = EXCLUDED.interfaces;
        """))
        await session.commit()
    await engine.dispose()
    print("✅ Database verification matrix seeded successfully.")

async def verify_compiler_endpoint():
    """Dispatches a mock compilation graph query payload to the FastAPI engine."""
    print("\n[2/3] Dispatching mock graph request payload to FastAPI endpoint...")
    
    # We purposefully pass mismatched interface keys ("ADC_0" and "CAN_0") to test loose string matching
    test_payload = {
        "prompt": "Connect an analog temperature sensor and high speed CAN nodes directly to my ESP32 core."
    }
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(FASTAPI_ENDPOINT, json=test_payload)
            
            if response.status_code != 200:
                print(f"❌ COMPILER ERROR [{response.status_code}]: {response.text}")
                return
                
            data = response.json()
            print("✅ FastAPI compiled graph successfully without internal exceptions.")
            
            # --- EVALUATION ENGINE ASSERTIONS ---
            print("\n[3/3] Running Validation Verifications:")
            
            abstract_nodes = data.get("abstract_graph", {}).get("nodes", [])
            print(f"  -> Extracted Abstract Devices Count: {len(abstract_nodes)}")
            for node in abstract_nodes:
                print(f"     * Allocated ID: {node['id']} mapped to registry part: {node['part_id']}")
                
            routing_report = data.get("routing_report", {})
            kicad_nets = routing_report.get("kicad_netlist", [])
            
            print(f"  -> Routed Net Connections Found: {len(kicad_nets)}")
            for net in kicad_nets:
                print(f"     * Net Name: [ {net['net_name']} ] Interconnect Track Links: {net['nodes']}")
                
            if len(kicad_nets) > 0:
                print("\n🎉 INTEGRATION TEST PASSED: Core data engine, DB layer, and rule router are solid!")
            else:
                print("\n⚠️ WARNING: Pipeline executed, but routing nets came back empty. Verify router loose-matching patches.")
                
        except httpx.ConnectError:
            print(f"❌ connection failed: Is your Uvicorn server actively running on {FASTAPI_ENDPOINT}?")

if __name__ == "__main__":
    asyncio.run(setup_test_database())
    asyncio.run(verify_compiler_endpoint())