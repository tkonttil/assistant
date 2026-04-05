#!/usr/bin/env python
"""Setup script for Home Assistant Migration Tool."""

from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="home-assistant-migration",
    version="0.1.0",
    description="A comprehensive tool for migrating and managing Home Assistant configurations",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Home Assistant Migration Tool",
    author_email="your@email.com",
    url="https://github.com/yourusername/home-assistant-migration",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.12",
    install_requires=[
        "HomeAssistant-API>=5.0.3",
        "pydantic>=2.12.5",
        "python-dotenv>=1.2.2",
        "toml>=0.10.2",
    ],
    entry_points={
        "console_scripts": [
            "migration-setup=home_assistant_migration.simple_migration:SimpleMigration.step1_setup",
            "migration-compute=home_assistant_migration.simple_migration:SimpleMigration.step2_compute",
            "migration-apply=home_assistant_migration.simple_migration:SimpleMigration.step3_apply",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
)