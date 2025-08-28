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
        type: str = None,
        description: str = None,
        hierarchy: str = None,
        role: str = None,
        property_index: str = None,
        properties_detailed: str = None,
        property_count: int = 0,
        method_index: str = None,
        methods_detailed: str = None,
        method_count: int = 0,
        url: str = None,
        is_collection: bool = False,
    ) -> Interface:
        """Add a new interface to the knowledge base."""
        interface = Interface(
            name=name,
            type=type,
            description=description,
            hierarchy=hierarchy,
            role=role,
            property_index=property_index,
            properties_detailed=properties_detailed,
            property_count=property_count,
            method_index=method_index,
            methods_detailed=methods_detailed,
            method_count=method_count,
            url=url,
            is_collection=is_collection,
        )
        self.db.add(interface)
        self.db.commit()
        self.db.refresh(interface)
        logger.info(f"Added interface: {name}")
        return interface

    def store_interface(self, interface_data: dict) -> Interface:
        """Store interface from dictionary data (used by scraper)."""
        # Calculate counts from detailed data
        property_count = 0
        if interface_data.get('properties_detailed'):
            try:
                properties = json.loads(interface_data['properties_detailed'])
                property_count = len(properties)
            except:
                property_count = 0
        
        method_count = 0
        if interface_data.get('methods_detailed'):
            try:
                methods = json.loads(interface_data['methods_detailed'])
                method_count = len(methods)
            except:
                method_count = 0
        
        return self.add_interface(
            name=interface_data.get("name"),
            type=interface_data.get("type"),
            description=interface_data.get("description"),
            hierarchy=interface_data.get("hierarchy"),
            role=interface_data.get("role"),
            property_index=interface_data.get("property_index"),
            properties_detailed=interface_data.get("properties_detailed"),
            property_count=property_count,
            method_index=interface_data.get("method_index"),
            methods_detailed=interface_data.get("methods_detailed"),
            method_count=method_count,
            url=interface_data.get("url"),
            is_collection=interface_data.get("is_collection", False),
        )

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

    def get_database_stats(self) -> dict:
        """Get comprehensive database statistics."""
        stats = {
            "total_interfaces": self.db.query(Interface).count(),
            "total_methods": self.db.query(Method).count(),
            "total_properties": self.db.query(Property).count(),
            "total_enums": self.db.query(Enum).count(),
            "total_typedefs": self.db.query(Typedef).count(),
            "interfaces_with_methods": self.db.query(Interface).filter(Interface.method_index.isnot(None)).count(),
            "interfaces_with_properties": self.db.query(Interface).filter(Interface.property_index.isnot(None)).count(),
            "collection_interfaces": self.db.query(Interface).filter(Interface.is_collection == True).count(),
            "object_interfaces": self.db.query(Interface).filter(Interface.type == "Object").count(),
            "total_property_count": self.db.query(Interface).with_entities(Interface.property_count).all(),
            "total_method_count": self.db.query(Interface).with_entities(Interface.method_count).all(),
        }
        
        # Calculate totals from count columns
        property_counts = [row[0] for row in stats["total_property_count"] if row[0] is not None]
        method_counts = [row[0] for row in stats["total_method_count"] if row[0] is not None]
        
        stats["total_properties_from_count"] = sum(property_counts)
        stats["total_methods_from_count"] = sum(method_counts)
        stats["avg_properties_per_interface"] = sum(property_counts) / len(property_counts) if property_counts else 0
        stats["avg_methods_per_interface"] = sum(method_counts) / len(method_counts) if method_counts else 0
        
        # Remove the raw data arrays
        del stats["total_property_count"]
        del stats["total_method_count"]
        
        return stats

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
