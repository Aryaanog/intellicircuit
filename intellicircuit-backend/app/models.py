from sqlalchemy import TEXT, Column, String, Numeric, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Component(Base):
    __tablename__ = "components"

    part_id = Column(String(100), primary_key=True)
    display_name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # mcu, sensor, power, etc.
    manufacturer_part_number = Column(String(100), nullable=True)
    
    vcc_min_v = Column(Numeric(4, 2), nullable=False)
    vcc_max_v = Column(Numeric(4, 2), nullable=False)
    typical_current_ma = Column(Numeric(8, 2), default=0.0)
    logic_level_v = Column(Numeric(4, 2), nullable=False)
    
    kicad_symbol = Column(String(150), nullable=False)
    kicad_footprint = Column(String(150), nullable=False)
    
    # Store pins, protocols, and buses natively
    interfaces = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# High-performance indexes matching RoadWatch-level optimization
Index('idx_components_category', Component.category)