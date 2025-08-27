"""
Database handler for CATIA V5 interface documentation knowledge base.
"""

from sqlalchemy.orm import Session
from .models import Interface, Method, Property, Enum, Typedef, get_db
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBaseHandler:
    """Handler for managing CATIA knowledge base operations."""

    def __init__(self):
        self.db = get_db()

    def add_interface(
        self,
        name: str,
        description: str = None,
        url: str = None,
        parent_interface: str = None,
        is_collection: bool = False,
    ) -> Interface:
        """Add a new interface to the knowledge base."""
        interface = Interface(
            name=name,
            description=description,
            url=url,
            parent_interface=parent_interface,
            is_collection=is_collection,
        )
        self.db.add(interface)
        self.db.commit()
        self.db.refresh(interface)
        logger.info(f"Added interface: {name}")
        return interface

    def get_interface(self, name: str) -> Interface:
        """Get interface by name."""
        return self.db.query(Interface).filter(Interface.name == name).first()

    def add_method(
        self,
        interface_name: str,
        name: str,
        signature: str = None,
        description: str = None,
        return_type: str = None,
        parameters: dict = None,
    ) -> Method:
        """Add a method to an interface."""
        interface = self.get_interface(interface_name)
        if not interface:
            raise ValueError(f"Interface {interface_name} not found")

        method = Method(
            interface_id=interface.id,
            name=name,
            signature=signature,
            description=description,
            return_type=return_type,
            parameters=json.dumps(parameters) if parameters else None,
        )
        self.db.add(method)
        self.db.commit()
        self.db.refresh(method)
        logger.info(f"Added method {name} to interface {interface_name}")
        return method

    def add_property(
        self,
        interface_name: str,
        name: str,
        property_type: str = None,
        description: str = None,
        is_readonly: bool = False,
    ) -> Property:
        """Add a property to an interface."""
        interface = self.get_interface(interface_name)
        if not interface:
            raise ValueError(f"Interface {interface_name} not found")

        property_obj = Property(
            interface_id=interface.id,
            name=name,
            property_type=property_type,
            description=description,
            is_readonly=is_readonly,
        )
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)
        logger.info(f"Added property {name} to interface {interface_name}")
        return property_obj

    def add_enum(self, name: str, description: str = None, values: dict = None) -> Enum:
        """Add an enumeration to the knowledge base."""
        enum = Enum(
            name=name,
            description=description,
            values=json.dumps(values) if values else None,
        )
        self.db.add(enum)
        self.db.commit()
        self.db.refresh(enum)
        logger.info(f"Added enum: {name}")
        return enum

    def add_typedef(
        self, name: str, type_definition: str, description: str = None
    ) -> Typedef:
        """Add a typedef to the knowledge base."""
        typedef = Typedef(
            name=name, type_definition=type_definition, description=description
        )
        self.db.add(typedef)
        self.db.commit()
        self.db.refresh(typedef)
        logger.info(f"Added typedef: {name}")
        return typedef

    def search_interfaces(self, query: str) -> list:
        """Search for interfaces by name or description."""
        return (
            self.db.query(Interface)
            .filter(
                (Interface.name.contains(query))
                | (Interface.description.contains(query))
            )
            .all()
        )

    def get_interface_methods(self, interface_name: str) -> list:
        """Get all methods for an interface."""
        interface = self.get_interface(interface_name)
        if interface:
            return interface.methods
        return []

    def get_interface_properties(self, interface_name: str) -> list:
        """Get all properties for an interface."""
        interface = self.get_interface(interface_name)
        if interface:
            return interface.properties
        return []

    def get_all_interfaces(self) -> list:
        """Get all interfaces."""
        return self.db.query(Interface).all()

    def get_interface_count(self) -> int:
        """Get total number of interfaces."""
        return self.db.query(Interface).count()

    def clear_database(self):
        """Clear all data from the database."""
        self.db.query(Method).delete()
        self.db.query(Property).delete()
        self.db.query(Interface).delete()
        self.db.query(Enum).delete()
        self.db.query(Typedef).delete()
        self.db.commit()
        logger.info("Database cleared")

    def __del__(self):
        """Close database session."""
        if hasattr(self, "db"):
            self.db.close()
