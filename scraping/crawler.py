"""
Main script to crawl CATIA V5 documentation and store in knowledge base.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from complete_scraper import CompleteCATIAScraper
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
    scraper = CompleteCATIAScraper()

    # Initialize knowledge base handler
    kb_handler = KnowledgeBaseHandler()

    try:
        logger.info("Starting CATIA documentation crawl...")

        # Clear existing data
        logger.info("Clearing existing database...")
        kb_handler.clear_database()

        # Choose processing mode
        import sys

        if len(sys.argv) > 1 and sys.argv[1] == "--full":
            # Full discovery mode - discover all interfaces
            logger.info("Full discovery mode - finding all CATIA interfaces...")
            interface_urls = scraper.discover_interface_urls()

            # Limit to first 50 for initial full run (can be increased)
            max_interfaces = 50
            if len(interface_urls) > max_interfaces:
                logger.info(
                    f"Limiting to first {max_interfaces} interfaces (found {len(interface_urls)} total)"
                )
                interface_urls = interface_urls[:max_interfaces]
        else:
            # Test mode - use specific interfaces
            logger.info("Test mode - processing specific interfaces...")
            interface_urls = [
                "http://catiadoc.free.fr/online/interfaces/interface_ABQAnalysisCase.htm",
                "http://catiadoc.free.fr/online/interfaces/interface_Application.htm",
                "http://catiadoc.free.fr/online/interfaces/interface_Document.htm",
                "http://catiadoc.free.fr/online/interfaces/interface_Part.htm",
                "http://catiadoc.free.fr/online/interfaces/interface_Product.htm",
            ]

        logger.info(f"Processing {len(interface_urls)} interfaces...")

        # Store in database
        stored_count = 0
        for url in interface_urls:
            try:
                # Scrape the interface
                interface_data = scraper.scrape_interface(url)

                if "error" in interface_data:
                    logger.error(f"Error scraping {url}: {interface_data['error']}")
                    continue

                # Convert inheritance hierarchy to parent interface
                parent_interface = None
                if interface_data["inheritance_hierarchy"]:
                    # Use the direct parent (second to last in hierarchy)
                    if len(interface_data["inheritance_hierarchy"]) > 1:
                        parent_interface = interface_data["inheritance_hierarchy"][-2]

                # Add interface
                interface = kb_handler.add_interface(
                    name=interface_data["interface_name"],
                    description=interface_data["description"],
                    url=interface_data["url"],
                    parent_interface=parent_interface,
                    is_collection="Collection" in interface_data["interface_name"],
                )

                # Add methods
                for method_data in interface_data["methods"]:
                    kb_handler.add_method(
                        interface_name=interface.name,
                        name=method_data["name"],
                        signature=f"{method_data['name']}()",
                        description=method_data["description"],
                        return_type=None,
                        parameters=None,
                    )

                # Add properties
                for property_data in interface_data["properties"]:
                    kb_handler.add_property(
                        interface_name=interface.name,
                        name=property_data["name"],
                        property_type=property_data["type"],
                        description=property_data["description"],
                        is_readonly=property_data["access_mode"] == "Read Only",
                    )

                stored_count += 1
                if stored_count % 1 == 0:  # Log each interface
                    logger.info(
                        f"Processed {stored_count}/{len(interface_urls)} interfaces"
                    )

            except Exception as e:
                logger.error(
                    f"Error storing interface {interface_data.get('interface_name', 'Unknown')}: {e}"
                )
                continue

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
