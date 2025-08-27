"""
Database models for CATIA V5 interface documentation knowledge base.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()


class Interface(Base):
    """Model for CATIA interfaces."""

    __tablename__ = "interfaces"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    url = Column(String(500))
    parent_interface = Column(String(255))  # For inheritance
    is_collection = Column(Boolean, default=False)

    # Relationships
    methods = relationship(
        "Method", back_populates="interface", cascade="all, delete-orphan"
    )
    properties = relationship(
        "Property", back_populates="interface", cascade="all, delete-orphan"
    )


class Method(Base):
    """Model for interface methods."""

    __tablename__ = "methods"

    id = Column(Integer, primary_key=True)
    interface_id = Column(Integer, ForeignKey("interfaces.id"), nullable=False)
    name = Column(String(255), nullable=False)
    signature = Column(Text)
    description = Column(Text)
    return_type = Column(String(255))
    parameters = Column(Text)  # JSON string of parameters

    # Relationship
    interface = relationship("Interface", back_populates="methods")


class Property(Base):
    """Model for interface properties."""

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True)
    interface_id = Column(Integer, ForeignKey("interfaces.id"), nullable=False)
    name = Column(String(255), nullable=False)
    property_type = Column(String(255))
    description = Column(Text)
    is_readonly = Column(Boolean, default=False)

    # Relationship
    interface = relationship("Interface", back_populates="properties")


class Enum(Base):
    """Model for enumerations."""

    __tablename__ = "enums"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    values = Column(Text)  # JSON string of enum values


class Typedef(Base):
    """Model for type definitions."""

    __tablename__ = "typedefs"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    type_definition = Column(String(255))
    description = Column(Text)


# Database setup
import os

db_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "databases", "knowledge.db"
)
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
