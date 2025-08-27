"""
Web scraper for CATIA V5 documentation.
Crawls the provided URLs and extracts interface information.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CATIADocumentationScraper:
    """Scraper for CATIA V5 documentation websites."""

    def __init__(self, base_urls: List[str], delay: float = 1.0):
        """
        Initialize the scraper.

        Args:
            base_urls: List of base URLs to start crawling from
            delay: Delay between requests to be respectful to the server
        """
        self.base_urls = base_urls
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        self.visited_urls: Set[str] = set()
        self.interface_urls: List[str] = []

    def get_page_content(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)  # Be respectful
            return BeautifulSoup(response.content, "lxml")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_interface_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract interface links from a page."""
        interface_links = []

        # Look for links in the main content area (more specific targeting)
        main_content = soup.find("div", class_="content") or soup.find("body")
        if main_content:
            for link in main_content.find_all("a", href=True):
                href = link.get("href")
                if href and href.endswith(".htm") and not href.startswith("http"):
                    # Check if it's likely an interface link by examining link text or context
                    link_text = link.get_text().strip()
                    if (
                        len(link_text) > 2
                        and link_text[0].isupper()
                        and not any(
                            word in href.lower()
                            for word in ["index", "tree", "main", "home", "deprecated"]
                        )
                    ):
                        full_url = urljoin(base_url, href)
                        if full_url not in self.visited_urls:
                            interface_links.append(full_url)

        # Also check for links in lists/tables which are common in index pages
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if href and href.endswith(".htm") and not href.startswith("http"):
                link_text = link.get_text().strip()
                # Look for patterns that indicate interface links
                if (
                    link_text
                    and len(link_text) > 2
                    and (link_text[0].isupper() or "::" in link_text)
                    and not any(
                        skip in href.lower()
                        for skip in [
                            "index",
                            "tree",
                            "main",
                            "home",
                            "deprecated",
                            "css",
                            "js",
                        ]
                    )
                ):
                    full_url = urljoin(base_url, href)
                    if full_url not in self.visited_urls:
                        interface_links.append(full_url)

        return interface_links

    def parse_main_index(self, url: str) -> List[str]:
        """Parse main index page to extract all interface links."""
        soup = self.get_page_content(url)
        if not soup:
            return []

        interface_links = self.extract_interface_links(soup, url)
        logger.info(f"Found {len(interface_links)} interface links on {url}")
        return interface_links

    def parse_interface_page(self, url: str) -> Dict:
        """Parse an individual interface documentation page."""
        soup = self.get_page_content(url)
        if not soup:
            return None

        interface_data = {
            "name": "",
            "description": "",
            "url": url,
            "parent_interface": None,
            "methods": [],
            "properties": [],
            "inheritance": [],
        }

        try:
            # Extract interface name from title or headings
            title = soup.find("title")
            if title:
                title_text = title.get_text().strip()
                # Extract interface name from title (usually "Interface InterfaceName")
                if "Interface" in title_text:
                    interface_data["name"] = title_text.split("Interface")[-1].strip()
                else:
                    interface_data["name"] = title_text

            # Also try to get name from h1 or h2 headings
            if not interface_data["name"]:
                h1 = soup.find("h1")
                if h1:
                    interface_data["name"] = h1.get_text().strip()
                else:
                    h2 = soup.find("h2")
                    if h2:
                        interface_data["name"] = h2.get_text().strip()

            # Extract description - look for various patterns
            description = ""

            # Try common description patterns
            desc_candidates = [
                soup.find("div", class_="description"),
                soup.find("p", class_="description"),
                soup.find("div", id="description"),
                soup.find(
                    "p", string=lambda text: text and len(text.strip()) > 50
                ),  # Long paragraphs
            ]

            for candidate in desc_candidates:
                if candidate:
                    text = candidate.get_text().strip()
                    if len(text) > len(description):
                        description = text

            # If no specific description found, try to get from first substantial paragraph
            if not description:
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 100 and not text.startswith("Copyright"):
                        description = text
                        break

            interface_data["description"] = description

            # Extract inheritance information - look for various patterns
            inheritance_section = (
                soup.find("dl", class_="inherits")
                or soup.find("div", class_="inheritance")
                or soup.find(
                    "p",
                    string=lambda text: "inherits" in text.lower() if text else False,
                )
            )

            if inheritance_section:
                inheritance_links = inheritance_section.find_all("a")
                if inheritance_links:
                    interface_data["inheritance"] = [
                        link.get_text().strip() for link in inheritance_links
                    ]
                    interface_data["parent_interface"] = (
                        inheritance_links[0].get_text().strip()
                    )
                else:
                    # Try to extract from text
                    text = inheritance_section.get_text()
                    if "inherits" in text.lower():
                        # Extract parent class name from text
                        import re

                        match = re.search(
                            r"inherits\s+from\s+(\w+)", text, re.IGNORECASE
                        )
                        if match:
                            interface_data["parent_interface"] = match.group(1)
                            interface_data["inheritance"] = [match.group(1)]

            # Extract methods - look for h2 with "Methods" and following content
            methods_h2 = None
            for h2 in soup.find_all("h2"):
                if "Methods" in h2.get_text():
                    methods_h2 = h2
                    break

            if methods_h2:
                # Get all content after the Methods h2 until the next h2
                methods_content = []
                current = methods_h2.find_next_sibling()
                while current and current.name != "h2":
                    methods_content.append(current)
                    current = current.find_next_sibling()

                # Parse method entries (lines starting with "o Func")
                for element in methods_content:
                    if hasattr(element, "get_text"):
                        text = element.get_text()
                        if "o Func" in text:
                            method_data = self._parse_method_from_text(text)
                            if method_data:
                                interface_data["methods"].append(method_data)

            # Extract properties - look for h2 with "Properties" and following content
            properties_h2 = None
            for h2 in soup.find_all("h2"):
                if "Properties" in h2.get_text():
                    properties_h2 = h2
                    break

            if properties_h2:
                # Get all content after the Properties h2 until the next h2
                properties_content = []
                current = properties_h2.find_next_sibling()
                while current and current.name != "h2":
                    properties_content.append(current)
                    current = current.find_next_sibling()

                # Parse property entries (using the raw HTML to get JavaScript)
                for element in properties_content:
                    if (
                        hasattr(element, "get_text")
                        and "o Property" in element.get_text()
                    ):
                        # Get both the text and raw HTML content
                        text = element.get_text()
                        html_content = str(element)
                        property_data = self._parse_property_from_html(
                            text, html_content
                        )
                        if property_data:
                            interface_data["properties"].append(property_data)

        except Exception as e:
            logger.error(f"Error parsing interface page {url}: {e}")

        return interface_data

    def _parse_method(self, method_section) -> Dict:
        """Parse a method section."""
        try:
            # Handle both div and dt/dd structures
            if method_section.name == "dt":
                method_name_elem = method_section
                method_desc_elem = method_section.find_next_sibling("dd")
            else:
                method_name_elem = (
                    method_section.find("h3")
                    or method_section.find("h4")
                    or method_section.find("strong")
                    or method_section.find("b")
                    or method_section
                )
                method_desc_elem = method_section

            if not method_name_elem:
                return None

            method_name = method_name_elem.get_text().strip()
            if not method_name or len(method_name) < 2:
                return None

            method_data = {
                "name": method_name,
                "signature": "",
                "description": "",
                "return_type": "",
                "parameters": [],
            }

            # Extract signature - look for code blocks or specific formatting
            signature_elem = (
                method_section.find("code")
                or method_section.find("pre")
                or method_section.find("div", class_="signature")
                or method_section.find("span", class_="signature")
            )

            if signature_elem:
                method_data["signature"] = signature_elem.get_text().strip()
            else:
                # Try to construct signature from method name
                method_data["signature"] = f"{method_name}()"

            # Extract description
            if method_desc_elem and method_desc_elem != method_name_elem:
                desc_text = method_desc_elem.get_text().strip()
                # Remove the method name from description if it's repeated
                if desc_text.startswith(method_name):
                    desc_text = desc_text[len(method_name) :].strip()
                if desc_text.startswith("(") and ")" in desc_text:
                    # Remove signature-like text from description
                    paren_end = desc_text.find(")") + 1
                    desc_text = desc_text[paren_end:].strip()
                method_data["description"] = desc_text

            # Extract parameters if available
            params_section = (
                method_section.find("dl", class_="parameters")
                or method_section.find("div", class_="parameters")
                or method_section.find("ul", class_="parameters")
            )

            if params_section:
                params = []
                param_items = (
                    params_section.find_all("li")
                    or params_section.find_all("dt")
                    or params_section.find_all("div")
                )

                for param_item in param_items:
                    param_text = param_item.get_text().strip()
                    if ":" in param_text:
                        name, desc = param_text.split(":", 1)
                        params.append(
                            {
                                "name": name.strip(),
                                "description": desc.strip(),
                            }
                        )
                    else:
                        params.append(
                            {
                                "name": param_text,
                                "description": "",
                            }
                        )

                method_data["parameters"] = params

            # Extract return type - look for "As type" at the end or in JavaScript
            return_match = re.search(r"As\s+(\w+)", signature_text)
            if return_match:
                method_data["return_type"] = return_match.group(1)
            else:
                # Try to extract from JavaScript activateLink calls
                js_match = re.search(
                    r"activateLink\('([^']+)','[^']+'\)", signature_text
                )
                if js_match:
                    method_data["return_type"] = js_match.group(1)

            return method_data

        except Exception as e:
            logger.error(f"Error parsing method: {e}")
            return None

    def _parse_property(self, property_section) -> Dict:
        """Parse a property section."""
        try:
            # Handle both div and dt/dd structures
            if property_section.name == "dt":
                property_name_elem = property_section
                property_desc_elem = property_section.find_next_sibling("dd")
            else:
                property_name_elem = (
                    property_section.find("h3")
                    or property_section.find("h4")
                    or property_section.find("strong")
                    or property_section.find("b")
                    or property_section
                )
                property_desc_elem = property_section

            if not property_name_elem:
                return None

            property_name = property_name_elem.get_text().strip()
            if not property_name or len(property_name) < 2:
                return None

            property_data = {
                "name": property_name,
                "type": "",
                "description": "",
                "readonly": False,
            }

            # Extract type - look for type information
            type_elem = (
                property_section.find("span", class_="type")
                or property_section.find("div", class_="type")
                or property_section.find("code")
                or property_section.find("em")
            )

            if type_elem:
                property_data["type"] = type_elem.get_text().strip()
            else:
                # Try to extract type from description or signature
                desc_text = (
                    property_desc_elem.get_text().strip() if property_desc_elem else ""
                )
                if ":" in desc_text:
                    type_part = desc_text.split(":")[0].strip()
                    property_data["type"] = type_part

            # Extract description
            if property_desc_elem and property_desc_elem != property_name_elem:
                desc_text = property_desc_elem.get_text().strip()
                # Remove property name and type from description if present
                if desc_text.startswith(property_name):
                    desc_text = desc_text[len(property_name) :].strip()
                if property_data["type"] and desc_text.startswith(
                    property_data["type"]
                ):
                    desc_text = desc_text[len(property_data["type"]) :].strip()
                if desc_text.startswith(":"):
                    desc_text = desc_text[1:].strip()
                property_data["description"] = desc_text

            # Check if readonly - look for readonly indicators
            section_text = property_section.get_text().lower()
            property_data["readonly"] = (
                "readonly" in section_text
                or "read-only" in section_text
                or "const" in section_text
            )

            return property_data

        except Exception as e:
            logger.error(f"Error parsing property: {e}")
            return None

    def _parse_method_from_text(self, text: str) -> Dict:
        """Parse a method from CATIA documentation text format."""
        try:
            # Extract method signature from "o Func ..." pattern
            if "o Func" not in text:
                return None

            method_data = {
                "name": "",
                "signature": "",
                "description": "",
                "return_type": "",
                "parameters": [],
            }

            # Extract method name and signature
            func_start = text.find("o Func")
            if func_start == -1:
                return None

            signature_text = text[func_start:].split("\n")[0].strip()
            method_data["signature"] = signature_text

            # Extract method name - look for the function name after "o Func"
            import re

            name_match = re.search(r"o Func\s+(\w+)", signature_text)
            if name_match:
                method_data["name"] = name_match.group(1)

            # Extract return type - look for "As type" at the end
            return_match = re.search(r"As\s+(\w+)", signature_text)
            if return_match:
                method_data["return_type"] = return_match.group(1)

            # Extract description - everything after the signature line
            lines = text.split("\n")
            description_lines = []
            in_description = False

            for line in lines:
                line = line.strip()
                if line.startswith("o Func"):
                    in_description = True
                    continue
                elif line.startswith("o ") and in_description:
                    break  # Next method/property starts
                elif in_description and line and not line.startswith("- **"):
                    description_lines.append(line)

            method_data["description"] = " ".join(description_lines).strip()

            # Extract parameters - look for "- **ParameterName**" patterns
            param_matches = re.findall(
                r"- \*\*(\w+)\*\*\s*(.*?)(?=\n- \*\*\w+\*\*|$)", text, re.DOTALL
            )
            for param_name, param_desc in param_matches:
                method_data["parameters"].append(
                    {"name": param_name, "description": param_desc.strip()}
                )

            return method_data

        except Exception as e:
            logger.error(f"Error parsing method from text: {e}")
            return None

    def _parse_property_from_html(self, text: str, html_content: str) -> Dict:
        """Parse a property from CATIA documentation text and HTML format."""
        try:
            # Extract property from "o Property ..." pattern
            if "o Property" not in text:
                return None

            property_data = {
                "name": "",
                "type": "",
                "description": "",
                "readonly": False,
            }

            # Try to extract type from JavaScript activateLink calls in the HTML
            import re

            js_match = re.search(r"activateLink\('([^']+)','[^']+'\)", html_content)
            if js_match:
                property_data["type"] = js_match.group(1)

            # Extract property name - look for the property name after "o Property"
            name_match = re.search(r"o Property\s+(\w+)", text)
            if name_match:
                property_data["name"] = name_match.group(1)

            # Extract description - everything after the signature line
            lines = text.split("\n")
            description_lines = []
            in_description = False

            for line in lines:
                line = line.strip()
                if line.startswith("o Property"):
                    in_description = True
                    continue
                elif line.startswith("o ") and in_description:
                    break  # Next method/property starts
                elif in_description and line and not line.startswith("- **"):
                    description_lines.append(line)

            property_data["description"] = " ".join(description_lines).strip()

            # Check if readonly - look for readonly indicators in the text
            property_data["readonly"] = (
                "readonly" in text.lower()
                or "read-only" in text.lower()
                or "const" in text.lower()
            )

            return property_data

        except Exception as e:
            logger.error(f"Error parsing property from HTML: {e}")
            return None

    def _parse_property_from_text(self, text: str) -> Dict:
        """Parse a property from CATIA documentation text format."""
        try:
            # Extract property from "o Property ..." pattern
            if "o Property" not in text:
                return None

            property_data = {
                "name": "",
                "type": "",
                "description": "",
                "readonly": False,
            }

            # Try to extract type from JavaScript activateLink calls in the raw text
            import re

            js_match = re.search(r"activateLink\('([^']+)','[^']+'\)", text)
            if js_match:
                property_data["type"] = js_match.group(1)

            # Extract property name - look for the property name after "o Property"
            name_match = re.search(r"o Property\s+(\w+)", text)
            if name_match:
                property_data["name"] = name_match.group(1)

            # Extract description - everything after the signature line
            lines = text.split("\n")
            description_lines = []
            in_description = False

            for line in lines:
                line = line.strip()
                if line.startswith("o Property"):
                    in_description = True
                    continue
                elif line.startswith("o ") and in_description:
                    break  # Next method/property starts
                elif in_description and line and not line.startswith("- **"):
                    description_lines.append(line)

            property_data["description"] = " ".join(description_lines).strip()

            # Check if readonly - look for readonly indicators in the text
            property_data["readonly"] = (
                "readonly" in text.lower()
                or "read-only" in text.lower()
                or "const" in text.lower()
            )

            return property_data

        except Exception as e:
            logger.error(f"Error parsing property from text: {e}")
            return None

    def crawl_documentation(self) -> List[Dict]:
        """Main crawling method."""
        all_interfaces = []

        # Prioritize the main index page for comprehensive interface discovery
        main_index_url = "http://catiadoc.free.fr/online/interfaces/main.htm"

        logger.info(f"Starting crawl from main index: {main_index_url}")

        # Get interface links from main index page first
        interface_links = self.parse_main_index(main_index_url)
        self.interface_urls.extend(interface_links)

        # Also check other provided URLs for additional links
        for base_url in self.base_urls:
            if base_url != main_index_url:
                logger.info(f"Checking additional URL: {base_url}")
                additional_links = self.parse_main_index(base_url)
                self.interface_urls.extend(additional_links)

        # Remove duplicates and filter out non-interface links
        self.interface_urls = list(set(self.interface_urls))
        logger.info(f"Total unique interface URLs found: {len(self.interface_urls)}")

        # Parse each interface page
        parsed_count = 0
        max_interfaces = 20  # Limit to first 20 interfaces for testing
        for url in self.interface_urls[:max_interfaces]:  # Only process first 20 URLs
            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            interface_data = self.parse_interface_page(url)

            if (
                interface_data and interface_data["name"]
            ):  # Only add if we got a valid interface
                all_interfaces.append(interface_data)
                parsed_count += 1
                logger.info(
                    f"Parsed interface: {interface_data['name']} ({parsed_count}/{max_interfaces})"
                )

        logger.info(
            f"Successfully parsed {len(all_interfaces)} interfaces out of {len(self.interface_urls)} URLs"
        )
        return all_interfaces

    def save_to_json(self, interfaces: List[Dict], filename: str):
        """Save parsed interfaces to JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(interfaces, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(interfaces)} interfaces to {filename}")
