# CATIA V5 Interface Documentation Scraper

A comprehensive Python system for scraping and extracting CATIA V5 interface documentation, creating a searchable knowledge base with enhanced HTML-based extraction techniques.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project provides an advanced web scraping system that extracts comprehensive CATIA V5 interface documentation from http://catiadoc.free.fr/. Using sophisticated HTML parsing and pattern recognition, it captures detailed information about:

- **Interfaces** with complete inheritance hierarchies and type information
- **Properties** with detailed descriptions, types, and access patterns
- **Methods** with comprehensive signatures, parameters, and return types
- **Collections** and their relationships
- **Hierarchical relationships** with full inheritance chains

The scraped data is stored in an optimized SQLite database with property and method counts for efficient querying and analysis.

## Key Features

- 🔍 **Enhanced HTML Extraction**: Advanced BeautifulSoup-based parsing with pattern recognition
- 🏗️ **Complete Inheritance Mapping**: Reconstructs full inheritance chains from documentation
- 📊 **Smart Type Detection**: Extracts property types from JavaScript `activateLink()` calls and HTML content
- 🗄️ **Optimized Database**: SQLite backend with count columns and performance indexes
- 🔗 **Clean Python API**: Easy-to-use SQLAlchemy-based interface for data access
- ⚡ **Full-Scale Processing**: Processes all ~993 discovered CATIA interfaces
- 📈 **Progress Tracking**: Detailed logging with statistics and error reporting
- 🛠️ **Robust Error Handling**: Graceful handling of malformed HTML and network issues

## Installation

### Using pip (recommended)

```bash
# Install from source
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Using Poetry

```bash
poetry install
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/oscik559/Project_CAD.git
cd Project_CAD

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Scrape CATIA Documentation

```bash
# Run the enhanced interface scraper (scrapes all ~993 interfaces)
python scraping/interface_index_scraper.py

# The scraper will automatically:
# - Discover all available CATIA interfaces
# - Extract detailed properties and methods using HTML parsing
# - Save results to SQLite database with count statistics
# - Provide progress tracking and summary statistics
```

### 2. Query the Database

```python
from scraping.db_handler import KnowledgeBaseHandler

# Initialize the knowledge base
handler = KnowledgeBaseHandler()

# Get database statistics
stats = handler.get_database_stats()
print(f"Total interfaces: {stats['total_interfaces']}")
print(f"Average properties per interface: {stats['avg_properties']:.1f}")
print(f"Average methods per interface: {stats['avg_methods']:.1f}")

# Search for interfaces
interfaces = handler.search_interfaces("Analysis")
for interface in interfaces:
    print(f"- {interface.name}: {interface.property_count} properties, {interface.method_count} methods")

# Get specific interface details
interface = handler.get_interface_by_name("ABQAnalysisCase")
if interface:
    properties = json.loads(interface.properties_detailed)
    methods = json.loads(interface.methods_detailed)
    print(f"Interface: {interface.name}")
    print(f"Properties: {len(properties)}")
    print(f"Methods: {len(methods)}")
```

## Project Structure

```text
Project_CAD/
├── scraping/                     # Core scraping package
│   ├── interface_index_scraper.py  # Enhanced HTML-based interface scraper
│   ├── db_handler.py            # Database operations and queries
│   ├── models.py                # SQLAlchemy models with count columns
│   └── README.md                # Package documentation
├── config/                      # Configuration files
│   ├── catia_config.yaml       # CATIA-specific settings
│   └── config.yaml             # General configuration
├── data/                        # Data storage
│   ├── cad_manuals/            # Source documentation
│   └── output_parts/           # Generated outputs
├── database/                   # SQLite database storage
│   └── knowledge_new.db        # Enhanced knowledge base with count statistics
├── docs/                       # Project documentation
│   ├── project_summary.md      # Technical overview
│   ├── research_notes.md       # Development notes
│   └── diagrams/               # Architecture diagrams
├── tests/                      # Test suite
│   └── mock_data/              # Test data and fixtures
├── pyproject.toml             # Modern Python packaging configuration
├── requirements.txt           # Production dependencies
├── setup.py                   # Legacy setuptools configuration
└── README.md                  # This file
```

## API Reference

### KnowledgeBaseHandler Class

The main interface for querying the scraped CATIA documentation database.

#### Core Methods

##### `get_database_stats() -> Dict`

Get comprehensive database statistics including counts and averages.

```python
from scraping.db_handler import KnowledgeBaseHandler

handler = KnowledgeBaseHandler()
stats = handler.get_database_stats()
print(f"Total interfaces: {stats['total_interfaces']}")
print(f"Total properties: {stats['total_properties']}")
print(f"Average properties per interface: {stats['avg_properties']:.1f}")
```

##### `search_interfaces(query: str) -> List[Interface]`

Search for interfaces by name using partial matching.

```python
results = handler.search_interfaces("Analysis")
for interface in results:
    print(f"- {interface.name}: {interface.property_count} properties")
```

##### `get_interface_by_name(name: str) -> Optional[Interface]`

Get detailed information about a specific interface.

```python
interface = handler.get_interface_by_name("ABQAnalysisCase")
if interface:
    print(f"Type: {interface.type}")
    print(f"URL: {interface.url}")
    properties = json.loads(interface.properties_detailed)
    methods = json.loads(interface.methods_detailed)
    print(f"Properties: {len(properties)}")
    print(f"Methods: {len(methods)}")
```

##### `get_all_interfaces() -> List[Interface]`

Retrieve all interfaces from the database.

##### `store_interface(interface_data: Dict) -> None`

Store a new interface in the database with automatic count calculation.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database configuration
DATABASE_URL=sqlite:///database/knowledge.db

# Scraping configuration
CATIA_BASE_URL=http://catiadoc.free.fr/online/interfaces/
REQUEST_DELAY=1.0
MAX_RETRIES=3
```

### YAML Configuration

Configure scraping behavior in `config/catia_config.yaml`:

```yaml
scraping:
  base_url: "http://catiadoc.free.fr/online/interfaces/"
  index_url: "http://catiadoc.free.fr/online/interfaces/CAAInterfaceIdx.htm"
  delay_between_requests: 1.0
  max_retries: 3
  timeout: 30

database:
  path: "database/knowledge.db"
  echo_sql: false

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Advanced Usage

### Custom Scraping

```python
from scraping.interface_index_scraper import InterfaceIndexScraper
from scraping.db_handler import KnowledgeBaseHandler

# Initialize components
scraper = InterfaceIndexScraper()
handler = KnowledgeBaseHandler()

# Discover all interface URLs
interface_urls = scraper.discover_interface_urls()
print(f"Found {len(interface_urls)} interfaces to scrape")

# Scrape specific interface
interface_data = scraper.scrape_interface_details({
    'url': 'http://catiadoc.free.fr/online/interfaces/interface_ABQAnalysisCase.htm',
    'name': 'ABQAnalysisCase'
})
print(f"Scraped: {interface_data['name']}")

# Store in database
handler.store_interface(interface_data)
```

### Database Direct Access

```python
from scraping.db_handler import KnowledgeBaseHandler
import json

handler = KnowledgeBaseHandler()

# Get all interfaces with detailed information
interfaces = handler.get_all_interfaces()
for interface in interfaces:
    print(f"{interface.name}: {interface.property_count} properties, {interface.method_count} methods")

# Search with custom filters
matching = handler.search_interfaces("Step")
print(f"Found {len(matching)} interfaces containing 'Step'")

# Access detailed property and method data
interface = handler.get_interface_by_name("ABQAnalysisCase")
if interface:
    properties = json.loads(interface.properties_detailed)
    methods = json.loads(interface.methods_detailed)
    print(f"First property: {properties[0]['name']}")
    print(f"First method: {methods[0]['name']}")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraping --cov-report=html

# Run specific test file
pytest tests/test_scraper.py
```

### Code Formatting

```bash
# Format code with Black
black scraping/ tests/

# Check with flake8
flake8 scraping/ tests/

# Type checking with mypy
mypy scraping/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Examples

### Example 1: Find All Analysis-Related Interfaces

```python
from scraping.db_handler import KnowledgeBaseHandler
import json

handler = KnowledgeBaseHandler()

# Search for analysis interfaces
analysis_interfaces = handler.search_interfaces("Analysis")

for interface in analysis_interfaces:
    print(f"\n=== {interface.name} ===")
    print(f"Type: {interface.type}")
    print(f"Properties: {interface.property_count}")
    print(f"Methods: {interface.method_count}")

    # Show first few properties
    if interface.properties_detailed:
        properties = json.loads(interface.properties_detailed)
        for prop in properties[:3]:
            print(f"  - {prop['name']}: {prop.get('description', 'No description')}")
```

### Example 2: Export Interface Documentation

```python
import json
from scraping.db_handler import KnowledgeBaseHandler

handler = KnowledgeBaseHandler()

# Export specific interface to JSON
interface_name = "ABQAnalysisCase"
interface = handler.get_interface_by_name(interface_name)

if interface:
    export_data = {
        'name': interface.name,
        'type': interface.type,
        'url': interface.url,
        'hierarchy': json.loads(interface.hierarchy) if interface.hierarchy else [],
        'properties': json.loads(interface.properties_detailed) if interface.properties_detailed else [],
        'methods': json.loads(interface.methods_detailed) if interface.methods_detailed else [],
        'property_count': interface.property_count,
        'method_count': interface.method_count
    }

    with open(f"{interface_name}_documentation.json", "w") as f:
        json.dump(export_data, f, indent=2)
    print(f"Exported {interface_name} documentation to JSON")
```

### Example 3: Generate Interface Summary Report

```python
from scraping.db_handler import KnowledgeBaseHandler

handler = KnowledgeBaseHandler()
stats = handler.get_database_stats()

print("=== CATIA Interface Database Summary ===")
print(f"Total Interfaces: {stats['total_interfaces']}")
print(f"Total Properties: {stats['total_properties']}")
print(f"Total Methods: {stats['total_methods']}")
print(f"Average Properties per Interface: {stats['avg_properties']:.1f}")
print(f"Average Methods per Interface: {stats['avg_methods']:.1f}")

# Find interfaces with most properties
all_interfaces = handler.get_all_interfaces()
interface_props = [(interface.name, interface.property_count) for interface in all_interfaces]

# Sort by property count
interface_props.sort(key=lambda x: x[1], reverse=True)

print("\n=== Top 10 Interfaces by Property Count ===")
for name, prop_count in interface_props[:10]:
    print(f"{name}: {prop_count} properties")
```

## Performance Notes

- **Initial Scraping**: Full scraping of ~993 interfaces takes approximately 45-60 minutes
- **Database Size**: Enhanced database with count columns is approximately 8-12 MB for complete CATIA documentation
- **Query Performance**: All queries are optimized with SQLAlchemy ORM and database indexes
- **Memory Usage**: Scraper uses minimal memory with incremental processing and batch saving
- **Extraction Quality**: Enhanced HTML parsing provides significantly better data quality than regex-based methods

## Troubleshooting

### Common Issues

1. **Connection Timeouts**: Increase timeout in config or check internet connection
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Database Locked**: Ensure no other processes are accessing the database
4. **Encoding Issues**: Verify UTF-8 encoding is supported

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run scraper with debug output
python scraping/interface_index_scraper.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- CATIA V5 documentation provided by Dassault Systèmes
- Built with Python, SQLAlchemy, BeautifulSoup4, and Requests

## Support

For questions, issues, or contributions:

- 📧 Email: [Your Email]
- 🐛 Issues: [GitHub Issues](https://github.com/oscik559/Project_CAD/issues)
- 📖 Documentation: [Project Wiki](https://github.com/oscik559/Project_CAD/wiki)
