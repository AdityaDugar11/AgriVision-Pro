"""
Database Models
Define database table structures
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base # type: ignore
from datetime import datetime

# ============================================================================
# FARMER MODEL
# ============================================================================

class Farmer(Base):
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    location = Column(String(200))
    language = Column(String(20), default="hi")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crop_reports = relationship("CropReport", back_populates="farmer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Farmer(id={self.id}, name={self.name}, phone={self.phone})>"

# ============================================================================
# CROP REPORT MODEL
# ============================================================================

class CropReport(Base):
    __tablename__ = "crop_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    crop_name = Column(String(100))
    disease_name = Column(String(100))
    confidence_score = Column(Float, default=0.0)
    treatment = Column(Text)  # JSON string
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    farmer = relationship("Farmer", back_populates="crop_reports")
    
    def __repr__(self):
        return f"<CropReport(id={self.id}, disease={self.disease_name}, confidence={self.confidence_score})>"

# ============================================================================
# TREATMENT MODEL (Optional - for storing treatment recommendations)
# ============================================================================

class Treatment(Base):
    __tablename__ = "treatments"
    
    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(100), index=True)
    pesticide_name = Column(String(200))
    dosage = Column(String(100))
    application_method = Column(String(200))
    cost = Column(Float, default=0.0)
    local_dealer = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Treatment(disease={self.disease_name}, pesticide={self.pesticide_name})>"