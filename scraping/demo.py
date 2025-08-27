"""
Example usage of the CATIA Knowledge Base system.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.query_interface import CATIAKnowledgeBase


def main():
    """Demonstrate usage of the CATIA knowledge base."""

    kb = CATIAKnowledgeBase()

    print("=== CATIA V5 Knowledge Base Demo ===\n")

    # Get statistics
    stats = kb.get_statistics()
    print("Knowledge Base Statistics:")
    print(f"  Total Interfaces: {stats['total_interfaces']}")
    print(f"  Total Methods: {stats['total_methods']}")
    print(f"  Total Properties: {stats['total_properties']}")
    print(f"  Collection Interfaces: {stats['collection_interfaces']}\n")

    # Search for interfaces
    print("Searching for 'Document' interfaces:")
    results = kb.search_interfaces("Document")
    for result in results[:5]:  # Show first 5
        print(f"  - {result['name']}: {result['description'][:100]}...")

    if results:
        # Get detailed information about first result
        interface_name = results[0]["name"]
        print(f"\nGetting details for interface: {interface_name}")
        details = kb.get_interface_details(interface_name)

        if details:
            print(f"Description: {details['description'][:200]}...")
            print(f"Parent Interface: {details['parent_interface']}")
            print(f"Is Collection: {details['is_collection']}")
            print(f"Number of Methods: {len(details['methods'])}")
            print(f"Number of Properties: {len(details['properties'])}")

            # Show first few methods
            if details["methods"]:
                print("\nFirst few methods:")
                for method in details["methods"][:3]:
                    print(f"  - {method['name']}: {method['description'][:100]}...")

            # Show first few properties
            if details["properties"]:
                print("\nFirst few properties:")
                for prop in details["properties"][:3]:
                    print(
                        f"  - {prop['name']} ({prop['type']}): {prop['description'][:100]}..."
                    )

    # Find interfaces with specific methods
    print("\nFinding interfaces with 'Add' methods:")
    add_methods = kb.find_interfaces_by_method("Add")
    for result in add_methods[:5]:
        print(f"  - {result['interface']}.{result['method']}")

    # Get collections
    print("\nCollection interfaces:")
    collections = kb.get_collections()
    for collection in collections[:5]:
        print(f"  - {collection['name']}: {collection['description'][:100]}...")


if __name__ == "__main__":
    main()
