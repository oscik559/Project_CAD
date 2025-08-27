"""
Main script to crawl CATIA V5 documentation and store in knowledge base.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.scraper import CATIADocumentationScraper
from scraping.db_handler import KnowledgeBaseHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to crawl and store CATIA documentation."""

    # URLs to crawl
    base_urls = [
        "http://catiadoc.free.fr/online/interfaces/main.htm",
        "http://catiadoc.free.fr/online/interfaces/tree.htm",
        "http://catiadoc.free.fr/online/interfaces/CAAHomeIdx.htm",
    ]

    # Initialize scraper
    scraper = CATIADocumentationScraper(base_urls, delay=1.0)

    # Initialize knowledge base handler
    kb_handler = KnowledgeBaseHandler()

    try:
        logger.info("Starting CATIA documentation crawl...")

        # Clear existing data
        logger.info("Clearing existing database...")
        kb_handler.clear_database()

        # Crawl documentation
        interfaces = scraper.crawl_documentation()

        logger.info(f"Found {len(interfaces)} interfaces to process")

        # Store in database (limit to first 20 for testing)
        stored_count = 0
        max_to_store = 20
        for interface_data in interfaces[
            :max_to_store
        ]:  # Only process first 20 interfaces
            try:
                # Add interface
                interface = kb_handler.add_interface(
                    name=interface_data["name"],
                    description=interface_data["description"],
                    url=interface_data["url"],
                    parent_interface=interface_data["parent_interface"],
                    is_collection="Collection" in interface_data["name"],
                )

                # Add methods
                for method_data in interface_data["methods"]:
                    kb_handler.add_method(
                        interface_name=interface.name,
                        name=method_data["name"],
                        signature=method_data["signature"],
                        description=method_data["description"],
                        return_type=method_data.get("return_type"),
                        parameters=method_data.get("parameters"),
                    )

                # Add properties
                for property_data in interface_data["properties"]:
                    kb_handler.add_property(
                        interface_name=interface.name,
                        name=property_data["name"],
                        property_type=property_data["type"],
                        description=property_data["description"],
                        is_readonly=property_data["readonly"],
                    )

                stored_count += 1
                if stored_count % 5 == 0:  # More frequent logging for smaller dataset
                    logger.info(
                        f"Processed {stored_count}/{min(len(interfaces), max_to_store)} interfaces"
                    )

            except Exception as e:
                logger.error(f"Error storing interface {interface_data['name']}: {e}")
                continue

        # Save to JSON as backup
        scraper.save_to_json(interfaces, "knowledge/catia_interfaces.json")

        # Print statistics
        total_interfaces = kb_handler.get_interface_count()
        logger.info("Crawling completed!")
        logger.info(f"Total interfaces stored: {total_interfaces}")

    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        raise
    finally:
        # Clean up
        if "kb_handler" in locals():
            kb_handler.db.close()


if __name__ == "__main__":
    main()
