"""
Comprehensive CATIA Interface Index Scraper
Extracts detailed information from each interface including type, hierarchy, role, etc.
"""

import requests
import re
import json
import logging
import sys
import os
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# Handle imports for both direct execution and module import
try:
    from .db_handler import KnowledgeBaseHandler
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scraping.db_handler import KnowledgeBaseHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterfaceIndexScraper:
    """Comprehensive scraper for CATIA interface index with detailed extraction."""

    def __init__(self):
        self.base_url = "http://catiadoc.free.fr/online/interfaces/"
        self.index_url = "http://catiadoc.free.fr/online/interfaces/CAAInterfaceIdx.htm"
        self.js_url = "http://catiadoc.free.fr/online/interfaces/jsTree.js"
        self.db_handler = KnowledgeBaseHandler()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # Cache for hierarchy lookup tables
        self._hierarchy_cache = None

    def _load_hierarchy_tables(self) -> tuple:
        """Load the JavaScript hierarchy lookup tables (cached)."""
        if self._hierarchy_cache is not None:
            return self._hierarchy_cache

        try:
            logger.info("Loading hierarchy lookup tables from JavaScript...")
            response = self.session.get(self.js_url, timeout=30)
            response.raise_for_status()
            js_content = response.text

            # Extract fatherLink entries: fatherLink["child"] = "parent"
            fatherlink_pattern = r"fatherLink\[(.*?)\]\s*=\s*(.*?);"
            fatherlink_matches = re.findall(fatherlink_pattern, js_content)

            # Extract father entries: father["child"] = "<a...>parent</a>"
            father_pattern = r"father\[(.*?)\]\s*=\s*(.*?);"
            father_matches = re.findall(father_pattern, js_content)

            # Clean up the entries by removing quotes
            fatherlink_dict = {}
            for child, parent in fatherlink_matches:
                child_clean = child.strip('"')
                parent_clean = parent.strip('"')
                fatherlink_dict[child_clean] = parent_clean

            father_dict = {}
            for child, parent_html in father_matches:
                child_clean = child.strip('"')
                parent_html_clean = parent_html.strip('"')

                # Extract the interface name from HTML link
                name_match = re.search(r">([^<]+)</a>", parent_html_clean)
                if name_match:
                    parent_name = name_match.group(1).replace("r1.", "").strip()
                    father_dict[child_clean] = parent_name

            self._hierarchy_cache = (fatherlink_dict, father_dict)
            logger.info(f"Loaded {len(fatherlink_dict)} hierarchy relationships")
            return self._hierarchy_cache

        except Exception as e:
            logger.error(f"Failed to load hierarchy tables: {e}")
            self._hierarchy_cache = ({}, {})
            return self._hierarchy_cache

    def discover_interface_urls(self) -> List[Dict[str, str]]:
        """Discover all interface URLs from the index page."""
        try:
            logger.info("Discovering interface URLs from index page...")
            response = self.session.get(self.index_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            interfaces = []

            # Find all interface links in the index
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if href and href.startswith("interface_") and href.endswith(".htm"):
                    interface_name = href.replace("interface_", "").replace(".htm", "")
                    full_url = self.base_url + href

                    # Get basic description from the index page
                    description = ""
                    link_parent = link.parent
                    if link_parent:
                        text_content = link_parent.get_text(strip=True)
                        # Extract description after the interface name
                        if "object" in text_content.lower():
                            parts = text_content.split("object", 1)
                            if len(parts) > 1:
                                description = parts[1].strip()

                    interfaces.append(
                        {
                            "name": interface_name,
                            "url": full_url,
                            "description": description,
                        }
                    )

            logger.info(f"Found {len(interfaces)} interface URLs")
            return interfaces

        except Exception as e:
            logger.error(f"Error discovering interface URLs: {e}")
            return []

    def extract_hierarchy(self, interface_name: str) -> List[str]:
        """Extract hierarchy using the JavaScript lookup tables (most accurate method)."""
        fatherlink_dict, father_dict = self._load_hierarchy_tables()

        if not fatherlink_dict:
            return []

        # Find the interface key in the lookup tables
        interface_key = None
        for key in fatherlink_dict.keys():
            if interface_name in key:
                interface_key = key
                break

        if not interface_key:
            logger.warning(f"Interface {interface_name} not found in hierarchy tables")
            return []

        # Build the complete hierarchy chain
        hierarchy = [interface_name]
        current_key = interface_key
        max_depth = 15  # Prevent infinite loops
        depth = 0

        while current_key in fatherlink_dict and depth < max_depth:
            parent_key = fatherlink_dict[current_key]
            if current_key in father_dict:
                parent_name = father_dict[current_key]
                hierarchy.append(parent_name)
                logger.debug(
                    f"Hierarchy: {current_key} -> {parent_key} ({parent_name})"
                )

            current_key = parent_key
            depth += 1

            # Stop if we've seen this key before (cycle detection)
            if parent_key in [fatherlink_dict.get(h, "") for h in hierarchy]:
                break

        # Reverse to get from base class to current interface
        hierarchy.reverse()

        logger.info(
            f"Extracted hierarchy for {interface_name}: {' → '.join(hierarchy)}"
        )
        return hierarchy

    def determine_interface_type(self, soup: BeautifulSoup, interface_name: str) -> str:
        """Determine the interface type."""
        page_text = soup.get_text()

        # Check for Collection type
        if "collection" in page_text.lower():
            return "Collection"

        # Check for explicit type mentions in parentheses
        type_pattern = rf"{re.escape(interface_name)}\s+\(([^)]+)\)"
        type_match = re.search(type_pattern, page_text, re.IGNORECASE)

        if type_match:
            type_text = type_match.group(1).strip()
            if type_text:
                return type_match.group(1).capitalize()

        # Default to Object for individual interfaces
        return "Object"

    def extract_role(self, soup: BeautifulSoup) -> str:
        """
        Extract role description using JavaScript-like approach: all content after <b>Role:</b> until second <hr> tag.
        """
        try:
            # Find all <hr> tags
            hr_tags = soup.find_all("hr")

            if len(hr_tags) < 2:
                return ""

            # Get content between first and second <hr>
            first_hr = hr_tags[0]
            second_hr = hr_tags[1]

            # Find <b>Role:</b> pattern anywhere between the hr tags
            current = first_hr.next_sibling
            role_found = False
            role_parts = []

            while current and current != second_hr:
                # Look for <b>Role:</b> pattern
                if hasattr(current, "name") and current.name == "b":
                    bold_text = current.get_text(strip=True)
                    if bold_text and bold_text.lower() in ["role:", "role"]:
                        role_found = True
                        # Skip to next element to start collecting role content
                        current = current.next_sibling
                        continue

                # If we found the Role marker, collect all subsequent content
                if role_found:
                    # Handle text nodes
                    if hasattr(current, "strip"):
                        text_content = str(current).strip()
                        if text_content and len(text_content) > 1:
                            role_parts.append(text_content)

                    # Handle element nodes
                    elif hasattr(current, "name") and current.name:
                        # Stop if we hit another <hr> tag
                        if current.name == "hr":
                            break

                        # Extract text from elements, including links
                        if current.name == "a":
                            link_text = current.get_text(strip=True)
                            if link_text:
                                role_parts.append(link_text)
                        elif hasattr(current, "get_text"):
                            element_text = current.get_text(strip=True)
                            if element_text and len(element_text) > 1:
                                role_parts.append(element_text)

                current = current.next_sibling

            # Process collected role parts
            if role_parts:
                role = " ".join(role_parts).strip()
                role = re.sub(r"\s+", " ", role)
                role = re.sub(r"^[:\s]+", "", role)

                if role and len(role) > 15:
                    if not role.endswith("."):
                        role += "."
                    return role

            return ""

        except Exception as e:
            logger.warning(f"Error extracting role: {e}")
            return ""

    def extract_description(self, soup: BeautifulSoup, interface_name: str) -> str:
        """
        Extract description from HTML structure between first and second <hr> tags.
        Focus on bold (<b>) and italic (<i>) text, handling reference items that may truncate descriptions.
        """
        try:
            # Find all <hr> tags
            hr_tags = soup.find_all("hr")

            if len(hr_tags) < 2:
                return ""

            # Get content between first and second <hr>
            first_hr = hr_tags[0]
            second_hr = hr_tags[1]

            # Collect text from bold and italic elements
            description_parts = []
            current = first_hr.next_sibling

            while current and current != second_hr:
                if hasattr(current, "name"):
                    # Extract text from <b> and <i> tags
                    if current.name in ["b", "i"]:
                        text = current.get_text(strip=True)
                        if text and len(text) > 3:
                            # Skip if it's the Role marker
                            if not (
                                current.name == "b"
                                and text.lower() in ["role:", "role"]
                            ):
                                description_parts.append(text)

                current = current.next_sibling

            if description_parts:
                description = " ".join(description_parts).strip()

                # Filter out reference items that might truncate the description
                if "(" in description and description.count("(") == description.count(
                    ")"
                ):
                    # Remove reference items in parentheses like "(see AnyObject)"
                    description = re.sub(r"\s*\([^)]*\)\s*", " ", description)

                # Clean up spacing
                description = re.sub(r"\s+", " ", description).strip()

                # Ensure it ends with a period if it doesn't already
                if description and not description.endswith("."):
                    description += "."

                return description

            return ""

        except Exception as e:
            logger.warning(f"Error extracting description from HTML structure: {e}")
            return ""

    def extract_properties(self, soup: BeautifulSoup) -> Dict[str, any]:
        """
        Extract properties using HTML structure approach - looking for PropertyIndex anchor and structured dt/dd elements.
        Returns dictionary with 'properties' list and 'count'.
        """
        properties = []

        try:
            # HTML Structure-based extraction
            prop_anchor = soup.find("a", {"name": "PropertyIndex"})
            if prop_anchor:
                # Start from the parent (h2 heading) and look for dt elements
                current = prop_anchor.parent
                sibling = current.next_sibling

                while sibling:
                    if hasattr(sibling, "name") and sibling.name == "dt":
                        # Extract properties from properly structured HTML
                        properties = self._extract_properties_from_html_structure(sibling)
                        break

                    elif hasattr(sibling, "name") and sibling.name in ["h2", "h3"]:
                        # Stop if we hit another section heading
                        section_text = sibling.get_text(strip=True)
                        if any(keyword in section_text for keyword in ["Method Index", "Example", "Returns"]):
                            break

                    sibling = sibling.next_sibling

            properties = properties[:15]  # Reasonable limit

        except Exception as e:
            logger.warning(f"Error in HTML approach for properties: {e}")

        logger.info(f"Found {len(properties)} properties using HTML approach")

        return {
            "properties": properties,
            "count": len(properties),
            "property_names": [prop["name"] for prop in properties],
            "property_index": (
                ", ".join([prop["name"] for prop in properties]) if properties else None
            ),
        }

    def extract_methods(self, soup: BeautifulSoup) -> Dict[str, any]:
        """
        Extract methods using HTML structure approach - looking for MethodIndex anchor and structured dt/dd elements.
        Returns dictionary with 'methods' list and 'count'.
        """
        methods = []

        try:
            # HTML Structure-based extraction
            method_anchor = soup.find("a", {"name": "MethodIndex"})
            if method_anchor:
                # Start from the parent (h2 heading) and look for dt elements
                current = method_anchor.parent
                sibling = current.next_sibling

                while sibling:
                    if hasattr(sibling, "name") and sibling.name == "dt":
                        # Extract methods from properly structured HTML
                        methods = self._extract_methods_from_html_structure(sibling)
                        break

                    elif hasattr(sibling, "name") and sibling.name in ["h2", "h3"]:
                        # Stop if we hit another section heading
                        section_text = sibling.get_text(strip=True)
                        if any(keyword in section_text for keyword in ["Property Index", "Example", "Returns"]):
                            break

                    sibling = sibling.next_sibling

            methods = methods[:20]  # Reasonable limit

        except Exception as e:
            logger.warning(f"Error in HTML approach for methods: {e}")

        logger.info(f"Found {len(methods)} methods using HTML approach")

        return {
            "methods": methods,
            "count": len(methods),
            "method_names": [method["name"] for method in methods],
            "method_index": (
                ", ".join([method["name"] for method in methods]) if methods else None
            ),
        }

    def _extract_methods_from_html_structure(self, dt_element) -> List[Dict[str, str]]:
        """
        Extract methods from structured HTML using dt/dd elements and links.
        This is the most reliable method for CATIA documentation.
        """
        methods = []
        
        try:
            # Find all links within the dt element - these are method names
            method_links = dt_element.find_all("a")
            
            for link in method_links:
                method_name = link.get_text(strip=True)
                
                # Find the corresponding description
                # Look for dd element that follows this link
                description = ""
                
                # Try to find the dd that contains the description for this method
                # Navigate from the link to find associated dd
                current = link.parent
                while current:
                    # Look for dd element at same level or nearby
                    dd = current.find_next("dd")
                    if dd:
                        # Get the text content and clean it
                        desc_text = dd.get_text(strip=True)
                        # Make sure this description belongs to our method
                        # (check that it doesn't contain another method name)
                        other_methods = [other_link.get_text(strip=True) for other_link in method_links if other_link != link]
                        
                        # If description doesn't start with another method name, it's likely ours
                        if not any(desc_text.startswith(other_method) for other_method in other_methods):
                            description = desc_text
                            break
                    
                    current = current.parent
                    if not current or current.name in ['body', 'html']:
                        break
                
                # Clean up description
                description = re.sub(r'\s+', ' ', description).strip()
                description = re.sub(r'^[^a-zA-Z]*', '', description)  # Remove leading non-letters
                
                if method_name and len(method_name) >= 2:
                    methods.append({
                        "name": method_name,
                        "description": description
                    })
            
        except Exception as e:
            logger.warning(f"Error in HTML structure extraction: {e}")
        
        return methods

    def _extract_properties_from_html_structure(self, dt_element) -> List[Dict[str, str]]:
        """
        Extract properties from structured HTML using dt/dd elements and links.
        This is the most reliable method for CATIA documentation.
        """
        properties = []
        
        try:
            # Find all links within the dt element - these are property names
            property_links = dt_element.find_all("a")
            
            for link in property_links:
                property_name = link.get_text(strip=True)
                
                # Find the corresponding description
                # Look for dd element that follows this link
                description = ""
                
                # Try to find the dd that contains the description for this property
                # Navigate from the link to find associated dd
                current = link.parent
                while current:
                    # Look for dd element at same level or nearby
                    dd = current.find_next("dd")
                    if dd:
                        # Get the text content and clean it
                        desc_text = dd.get_text(strip=True)
                        # Make sure this description belongs to our property
                        # (check that it doesn't contain another property name)
                        other_properties = [other_link.get_text(strip=True) for other_link in property_links if other_link != link]
                        
                        # If description doesn't start with another property name, it's likely ours
                        if not any(desc_text.startswith(other_prop) for other_prop in other_properties):
                            description = desc_text
                            break
                    
                    current = current.parent
                    if not current or current.name in ['body', 'html']:
                        break
                
                # Clean up description
                description = re.sub(r'\s+', ' ', description).strip()
                description = re.sub(r'^[^a-zA-Z]*', '', description)  # Remove leading non-letters
                
                if property_name and len(property_name) >= 2:
                    properties.append({
                        "name": property_name,
                        "description": description
                    })
            
        except Exception as e:
            logger.warning(f"Error in HTML structure extraction for properties: {e}")
        
        return properties

    def scrape_interface_details(
        self, interface_info: Dict[str, str]
    ) -> Dict[str, any]:
        """Scrape detailed information from a single interface page."""
        interface_name = interface_info["name"]
        url = interface_info["url"]

        logger.info(f"Scraping interface: {interface_name}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract all the required information using JavaScript-based hierarchy extraction
            hierarchy = self.extract_hierarchy(interface_name)
            properties_data = self.extract_properties(soup)
            methods_data = self.extract_methods(soup)
            role = self.extract_role(soup)
            interface_type = self.determine_interface_type(soup, interface_name)

            # Extract the description using HTML structure approach
            description = self.extract_description(soup, interface_name)

            # Determine if it's a collection
            is_collection = (
                interface_type == "Collection" or interface_name.lower().endswith("s")
            )

            return {
                "name": interface_name,
                "type": interface_type,
                "description": description,
                "hierarchy": json.dumps(hierarchy),
                "role": role,
                "property_index": properties_data["property_index"],
                "properties_detailed": (
                    json.dumps(properties_data["properties"])
                    if properties_data["properties"]
                    else None
                ),
                "method_index": methods_data["method_index"],
                "methods_detailed": (
                    json.dumps(methods_data["methods"])
                    if methods_data["methods"]
                    else None
                ),
                "url": url,
                "is_collection": is_collection,
            }

        except Exception as e:
            logger.error(f"Error scraping interface {interface_name}: {e}")
            return None

def main():
    """Main execution function."""
    scraper = InterfaceIndexScraper()

    # Clear the database at the start of each run
    print("🗑️ Clearing database...")
    try:
        scraper.db_handler.clear_database()
        print("✅ Database cleared successfully")
    except Exception as e:
        print(f"❌ Failed to clear database: {e}")
        return

    # Discover all interface URLs
    print("🔍 Discovering interface URLs...")
    interfaces = scraper.discover_interface_urls()

    if not interfaces:
        print("❌ No interfaces found!")
        return

    print(f"✅ Found {len(interfaces)} interfaces")

    # Scrape all discovered interfaces
    print(f"\n🚀 Scraping all {len(interfaces)} interfaces...")
    print("=" * 60)

    results = []
    saved_count = 0
    for i, interface_info in enumerate(interfaces, 1):
        print(f"\n{i}. Scraping: {interface_info['name']}")
        print("-" * 40)

        try:
            result = scraper.scrape_interface_details(interface_info)
            if result:
                results.append(result)

                # Save to database immediately after processing each interface
                try:
                    scraper.db_handler.store_interface(result)
                    saved_count += 1
                    print(f"✅ Success: {result['name']} (Saved to DB)")
                except Exception as db_error:
                    print(
                        f"✅ Success: {result['name']} (❌ DB Save Failed: {db_error})"
                    )

                print(f"   Type: {result['type']}")
                print(f"   Properties: {result.get('property_index', 'None')}")
                print(f"   Methods: {result.get('method_index', 'None')}")
                if result.get("hierarchy"):
                    hierarchy = json.loads(result["hierarchy"])
                    print(
                        f"   Hierarchy: {' → '.join(hierarchy[-3:])}"
                    )  # Show last 3 levels

                # Show progress every 10 interfaces
                if i % 10 == 0:
                    print(
                        f"\n📊 Progress Update: {i}/{len(interfaces)} processed, {saved_count} saved to database"
                    )

            else:
                print(f"❌ Failed to scrape {interface_info['name']}")

        except Exception as e:
            print(f"❌ Error scraping {interface_info['name']}: {e}")

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully scraped: {len(results)}/{len(interfaces)} interfaces")
    print(f"💾 Successfully saved to database: {saved_count}/{len(results)} interfaces")

    total_properties = sum(
        len(json.loads(r.get("properties_detailed", "[]")))
        for r in results
        if r.get("properties_detailed")
    )
    total_methods = sum(
        len(json.loads(r.get("methods_detailed", "[]")))
        for r in results
        if r.get("methods_detailed")
    )

    print(f"📝 Total properties extracted: {total_properties}")
    print(f"🛠️  Total methods extracted: {total_methods}")

    if results:
        avg_props = total_properties / len(results)
        avg_methods = total_methods / len(results)
        print(
            f"📈 Average per interface: {avg_props:.1f} properties, {avg_methods:.1f} methods"
        )

    print("\n🎉 Scraping completed!")


if __name__ == "__main__":
    main()
