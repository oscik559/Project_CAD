from setuptools import find_packages, setup

setup(
    name="agentic_reasoning",
    version="0.2.0",
    author="Oscar Chigozie Ikechukwu",
    description="Multi-agent system for CAD and reasoning tasks",
    # Ensure README is opened with UTF-8 to avoid encoding errors on Windows
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.9",
)
