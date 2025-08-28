# CATIA Documentation Scraper

A comprehensive Python system for scraping and extracting CATIA V5 documentation, creating a searchable knowledge base of interfaces, methods, and properties.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project provides a sophisticated web scraping system that extracts comprehensive CATIA V5 interface documentation from online sources. It captures detailed information about:

- **Interfaces** with complete inheritance hierarchies
- **Properties** with full type information and access modes
- **Methods** with signatures, parameters, and return types
- **Collections** and their relationships

The scraped data is stored in a SQLite database and accessed through a clean Python API for integration with other tools and workflows.

## Features

- 🔍 **Comprehensive Extraction**: Captures all interface details without data loss
- 🏗️ **Complete Inheritance**: Reconstructs full inheritance chains from documentation
- 📊 **Type-Aware**: Extracts property types from JavaScript `activateLink()` calls
- 🗄️ **Database Storage**: SQLite backend with SQLAlchemy ORM
- 🔗 **Clean API**: Easy-to-use query interface for accessing scraped data
- ⚡ **Dual Processing**: Test mode (limited) and full mode (comprehensive)
- 📈 **Progress Tracking**: Detailed logging and progress reporting

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
# Run full scraping (recommended for first time)
python scraping/crawler.py --full

# Or run in test mode (first 10 interfaces)
python scraping/crawler.py --test
```

### 2. Query the Database

```python
from scraping.query_interface import CATIAKnowledgeBase

# Initialize the knowledge base
kb = CATIAKnowledgeBase()

# Search for interfaces
results = kb.search_interfaces("ABQAnalysisCase")
print(f"Found {len(results)} interfaces")

# Get detailed interface information
details = kb.get_interface_details("ABQAnalysisCase")
print(f"Interface: {details['name']}")
print(f"Properties: {len(details['properties'])}")
print(f"Methods: {len(details['methods'])}")

# Get database statistics
stats = kb.get_statistics()
print(f"Total interfaces: {stats['total_interfaces']}")
print(f"Total properties: {stats['total_properties']}")
print(f"Total methods: {stats['total_methods']}")
```

## Project Structure

```
Project_CAD/
├── scraping/                 # Core scraping package
│   ├── complete_scraper.py   # Main scraper implementation
│   ├── crawler.py           # Entry point and orchestration
│   ├── db_handler.py        # Database operations
│   ├── models.py            # SQLAlchemy database models
│   ├── query_interface.py   # API for accessing scraped data
│   └── README.md            # Package documentation
├── config/                  # Configuration files
│   ├── catia_config.yaml   # CATIA-specific settings
│   └── config.yaml         # General configuration
├── data/                    # Data storage
│   ├── cad_manuals/        # Source documentation
│   └── output_parts/       # Generated outputs
├── database/               # SQLite database storage
│   └── knowledge.db        # Main knowledge base
├── docs/                   # Project documentation
├── tests/                  # Test suite
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## API Reference

### CATIAKnowledgeBase Class

The main interface for querying the scraped CATIA documentation.

#### Methods

##### `search_interfaces(query: str) -> List[Dict]`
Search for interfaces by name or description.

```python
results = kb.search_interfaces("Analysis")
for interface in results:
    print(f"- {interface['name']}: {interface['description']}")
```

##### `get_interface_details(interface_name: str) -> Optional[Dict]`
Get comprehensive details about a specific interface.

```python
details = kb.get_interface_details("ABQAnalysisCase")
print(f"Parent: {details['parent_interface']}")
print(f"URL: {details['url']}")

# Access properties
for prop in details['properties']:
    print(f"  Property: {prop['name']} ({prop['type']})")

# Access methods
for method in details['methods']:
    print(f"  Method: {method['name']} -> {method['return_type']}")
```

##### `get_interface_methods(interface_name: str) -> List[Dict]`
Get all methods for a specific interface.

##### `get_interface_properties(interface_name: str) -> List[Dict]`
Get all properties for a specific interface.

##### `get_statistics() -> Dict`
Get database statistics and overview.

```python
stats = kb.get_statistics()
print(f"Database contains:")
print(f"  - {stats['total_interfaces']} interfaces")
print(f"  - {stats['total_properties']} properties")
print(f"  - {stats['total_methods']} methods")
```

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
from scraping.complete_scraper import CompleteCATIAScraper
from scraping.db_handler import KnowledgeBaseHandler

# Initialize components
scraper = CompleteCATIAScraper()
db_handler = KnowledgeBaseHandler()

# Discover all interface URLs
urls = scraper.discover_interface_urls()
print(f"Found {len(urls)} interfaces to scrape")

# Scrape specific interface
interface_data = scraper.scrape_interface("http://catiadoc.free.fr/online/interfaces/interface_ABQAnalysisCase.htm")
print(f"Scraped: {interface_data['name']}")

# Store in database
db_handler.store_interface(interface_data)
```

### Database Direct Access

```python
from scraping.db_handler import KnowledgeBaseHandler

handler = KnowledgeBaseHandler()

# Raw database queries
interfaces = handler.get_all_interfaces()
for interface in interfaces:
    print(f"{interface.name}: {len(interface.properties)} properties")

# Search with custom filters
matching = handler.search_interfaces("Step")
print(f"Found {len(matching)} interfaces containing 'Step'")
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
from scraping.query_interface import CATIAKnowledgeBase

kb = CATIAKnowledgeBase()

# Search for analysis interfaces
analysis_interfaces = kb.search_interfaces("Analysis")

for interface in analysis_interfaces:
    details = kb.get_interface_details(interface['name'])
    print(f"\n=== {interface['name']} ===")
    print(f"Description: {interface['description']}")
    print(f"Properties: {len(details['properties'])}")
    print(f"Methods: {len(details['methods'])}")

    # Show first few properties
    for prop in details['properties'][:3]:
        access = "Read-only" if prop['readonly'] else "Read/Write"
        print(f"  - {prop['name']} ({prop['type']}) - {access}")
```

### Example 2: Export Interface Documentation

```python
import json
from scraping.query_interface import CATIAKnowledgeBase

kb = CATIAKnowledgeBase()

# Export specific interface to JSON
interface_name = "ABQAnalysisCase"
details = kb.get_interface_details(interface_name)

if details:
    with open(f"{interface_name}_documentation.json", "w") as f:
        json.dump(details, f, indent=2)
    print(f"Exported {interface_name} documentation to JSON")
```

### Example 3: Generate Interface Summary Report

```python
from scraping.query_interface import CATIAKnowledgeBase

kb = CATIAKnowledgeBase()
stats = kb.get_statistics()

print("=== CATIA Interface Database Summary ===")
print(f"Total Interfaces: {stats['total_interfaces']}")
print(f"Total Properties: {stats['total_properties']}")
print(f"Total Methods: {stats['total_methods']}")

# Find interfaces with most properties
all_interfaces = kb.search_interfaces("")  # Get all
interface_props = []

for interface in all_interfaces:
    details = kb.get_interface_details(interface['name'])
    interface_props.append((interface['name'], len(details['properties'])))

# Sort by property count
interface_props.sort(key=lambda x: x[1], reverse=True)

print("\n=== Top 10 Interfaces by Property Count ===")
for name, prop_count in interface_props[:10]:
    print(f"{name}: {prop_count} properties")
```

## Performance Notes

- **Initial Scraping**: Full scraping of ~1000 interfaces takes approximately 30-45 minutes
- **Database Size**: Typical database size is 5-10 MB for complete CATIA documentation
- **Query Performance**: All queries are optimized with database indexes
- **Memory Usage**: Scraper uses minimal memory with incremental processing

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
python scraping/crawler.py --full --debug
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