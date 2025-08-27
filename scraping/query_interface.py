"""
Query interface for CATIA V5 knowledge base.
Provides methods for agents to search and retrieve interface information.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.db_handler import KnowledgeBaseHandler
from typing import List, Dict, Optional
import json


class CATIAKnowledgeBase:
    """Interface for querying CATIA V5 knowledge base."""

    def __init__(self):
        self.handler = KnowledgeBaseHandler()

    def search_interfaces(self, query: str) -> List[Dict]:
        """Search for interfaces by name or description."""
        interfaces = self.handler.search_interfaces(query)
        return [
            {
                "name": interface.name,
                "description": interface.description,
                "url": interface.url,
                "parent_interface": interface.parent_interface,
                "is_collection": interface.is_collection,
            }
            for interface in interfaces
        ]

    def get_interface_details(self, interface_name: str) -> Optional[Dict]:
        """Get detailed information about a specific interface."""
        interface = self.handler.get_interface(interface_name)
        if not interface:
            return None

        methods = self.handler.get_interface_methods(interface_name)
        properties = self.handler.get_interface_properties(interface_name)

        return {
            "name": interface.name,
            "description": interface.description,
            "url": interface.url,
            "parent_interface": interface.parent_interface,
            "is_collection": interface.is_collection,
            "methods": [
                {
                    "name": method.name,
                    "signature": method.signature,
                    "description": method.description,
                    "return_type": method.return_type,
                    "parameters": (
                        json.loads(method.parameters) if method.parameters else []
                    ),
                }
                for method in methods
            ],
            "properties": [
                {
                    "name": prop.name,
                    "type": prop.property_type,
                    "description": prop.description,
                    "readonly": prop.is_readonly,
                }
                for prop in properties
            ],
        }

    def get_interface_methods(self, interface_name: str) -> List[Dict]:
        """Get all methods for a specific interface."""
        methods = self.handler.get_interface_methods(interface_name)
        return [
            {
                "name": method.name,
                "signature": method.signature,
                "description": method.description,
                "return_type": method.return_type,
                "parameters": (
                    json.loads(method.parameters) if method.parameters else []
                ),
            }
            for method in methods
        ]

    def get_interface_properties(self, interface_name: str) -> List[Dict]:
        """Get all properties for a specific interface."""
        properties = self.handler.get_interface_properties(interface_name)
        return [
            {
                "name": prop.name,
                "type": prop.property_type,
                "description": prop.description,
                "readonly": prop.is_readonly,
            }
            for prop in properties
        ]

    def find_interfaces_by_method(self, method_name: str) -> List[Dict]:
        """Find interfaces that have a specific method."""
        # This would require a more complex query, but for now we'll search through all interfaces
        all_interfaces = self.handler.get_all_interfaces()
        matching_interfaces = []

        for interface in all_interfaces:
            methods = self.handler.get_interface_methods(interface.name)
            for method in methods:
                if method_name.lower() in method.name.lower():
                    matching_interfaces.append(
                        {
                            "interface": interface.name,
                            "method": method.name,
                            "signature": method.signature,
                            "description": method.description,
                        }
                    )

        return matching_interfaces

    def find_interfaces_by_property(self, property_name: str) -> List[Dict]:
        """Find interfaces that have a specific property."""
        all_interfaces = self.handler.get_all_interfaces()
        matching_interfaces = []

        for interface in all_interfaces:
            properties = self.handler.get_interface_properties(interface.name)
            for prop in properties:
                if property_name.lower() in prop.name.lower():
                    matching_interfaces.append(
                        {
                            "interface": interface.name,
                            "property": prop.name,
                            "type": prop.property_type,
                            "description": prop.description,
                        }
                    )

        return matching_interfaces

    def get_inheritance_hierarchy(self, interface_name: str) -> List[str]:
        """Get the inheritance hierarchy for an interface."""
        interface = self.handler.get_interface(interface_name)
        if not interface:
            return []

        hierarchy = [interface_name]
        current = interface

        while current and current.parent_interface:
            hierarchy.append(current.parent_interface)
            current = self.handler.get_interface(current.parent_interface)

        return hierarchy

    def get_child_interfaces(self, interface_name: str) -> List[str]:
        """Get all interfaces that inherit from the specified interface."""
        all_interfaces = self.handler.get_all_interfaces()
        children = []

        for interface in all_interfaces:
            if interface.parent_interface == interface_name:
                children.append(interface.name)

        return children

    def get_collections(self) -> List[Dict]:
        """Get all collection interfaces."""
        all_interfaces = self.handler.get_all_interfaces()
        collections = []

        for interface in all_interfaces:
            if interface.is_collection:
                collections.append(
                    {
                        "name": interface.name,
                        "description": interface.description,
                        "url": interface.url,
                    }
                )

        return collections

    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge base."""
        total_interfaces = self.handler.get_interface_count()
        all_interfaces = self.handler.get_all_interfaces()

        total_methods = sum(
            len(self.handler.get_interface_methods(interface.name))
            for interface in all_interfaces
        )
        total_properties = sum(
            len(self.handler.get_interface_properties(interface.name))
            for interface in all_interfaces
        )

        collections = sum(1 for interface in all_interfaces if interface.is_collection)

        return {
            "total_interfaces": total_interfaces,
            "total_methods": total_methods,
            "total_properties": total_properties,
            "collection_interfaces": collections,
        }

    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, "handler"):
            self.handler.db.close()
