# CATIA V5 Knowledge Base

This module provides a comprehensive system for crawling, storing, and querying CATIA V5 interface documentation.

## Overview

The system consists of several components:

- **Web Scraper** (`scraper.py`): Crawls CATIA documentation websites and extracts interface information
- **Database Models** (`../database/models.py`): SQLAlchemy models for storing the knowledge base
- **Database Handler** (`../database/db_handler.py`): Manages database operations
- **Query Interface** (`query_interface.py`): Provides methods for agents to query the knowledge base
- **Main Crawler** (`crawler.py`): Orchestrates the crawling and storage process
- **Demo** (`demo.py`): Example usage of the system

## Features

- **Comprehensive Crawling**: Extracts interface information, methods, properties, and inheritance relationships
- **Structured Storage**: Stores data in SQLite database with proper relationships
- **Powerful Querying**: Search interfaces by name, method, property, or inheritance
- **Agent-Friendly**: Clean API for AI agents to access CATIA knowledge

## Usage

### 1. Crawl Documentation

To crawl the CATIA documentation and populate the knowledge base:

```bash
cd /path/to/project
python knowledge/crawler.py
```

This will:

- Crawl the provided URLs
- Extract interface information
- Store everything in the SQLite database
- Save a JSON backup file

### 2. Query the Knowledge Base

```python
from knowledge.query_interface import CATIAKnowledgeBase

kb = CATIAKnowledgeBase()

# Search for interfaces
results = kb.search_interfaces("Document")

# Get detailed interface information
details = kb.get_interface_details("PartDocument")

# Find interfaces with specific methods
methods = kb.find_interfaces_by_method("Add")

# Get inheritance hierarchy
hierarchy = kb.get_inheritance_hierarchy("Document")

# Get statistics
stats = kb.get_statistics()
```

### 3. Run Demo

```bash
python knowledge/demo.py
```

## Database Schema

The system uses the following main entities:

- **Interface**: CATIA interfaces with name, description, URL, and inheritance info
- **Method**: Interface methods with signatures, descriptions, and parameters
- **Property**: Interface properties with types and descriptions
- **Enum**: Enumeration types
- **Typedef**: Type definitions

## API Reference

### CATIAKnowledgeBase

#### Methods

- `search_interfaces(query: str)`: Search interfaces by name or description
- `get_interface_details(name: str)`: Get complete interface information
- `get_interface_methods(name: str)`: Get all methods for an interface
- `get_interface_properties(name: str)`: Get all properties for an interface
- `find_interfaces_by_method(method_name: str)`: Find interfaces with specific methods
- `find_interfaces_by_property(property_name: str)`: Find interfaces with specific properties
- `get_inheritance_hierarchy(name: str)`: Get inheritance chain
- `get_child_interfaces(name: str)`: Get interfaces that inherit from this one
- `get_collections()`: Get all collection interfaces
- `get_statistics()`: Get knowledge base statistics

## Configuration

The system is configured to crawl these URLs:

- `http://catiadoc.free.fr/online/interfaces/main.htm`
- `http://catiadoc.free.fr/online/interfaces/tree.htm`
- `http://catiadoc.free.fr/online/interfaces/CAAHomeIdx.htm`

You can modify the URLs in `crawler.py` if needed.

## Dependencies

- requests
- beautifulsoup4
- lxml
- sqlalchemy

Install with:

```bash
pip install requests beautifulsoup4 lxml sqlalchemy
```

## Output Files

- `database/knowledge.db`: SQLite database with all knowledge
- `knowledge/catia_interfaces.json`: JSON backup of crawled data

## Notes

- The crawler includes delays between requests to be respectful to the server
- All interface URLs are deduplicated automatically
- Error handling is included for robust crawling
- The system can handle large amounts of documentation data
