from setuptools import find_packages, setup

# Read requirements from requirements.txt
with open("requirements.txt", encoding="utf-8") as f:
    requirements = [
        line.strip() 
        for line in f 
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="catia-documentation-scraper",
    version="2.0.0",
    author="Oscar Chigozie Ikechukwu",
    author_email="oscik559@example.com",
    description="Enhanced CATIA V5 interface documentation scraper with advanced HTML parsing and database optimization",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/oscik559/Project_CAD",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0", 
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "catia-scraper=scraping.interface_index_scraper:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent", 
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Computer Aided Design",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.11",
    keywords=[
        "catia", "cad", "documentation", "scraping", "automation", 
        "html-parsing", "sqlalchemy", "database", "interface"
    ],
    project_urls={
        "Homepage": "https://github.com/oscik559/Project_CAD",
        "Repository": "https://github.com/oscik559/Project_CAD", 
        "Documentation": "https://github.com/oscik559/Project_CAD#readme",
        "Bug Reports": "https://github.com/oscik559/Project_CAD/issues",
    },
)
