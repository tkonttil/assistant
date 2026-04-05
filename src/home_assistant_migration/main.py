"""
Main script to fetch and store Home Assistant data.
"""

import os
from .hass_client import HassClient
from .storage import Storage


def main():
    """Main function to fetch and store Home Assistant data."""
    print("Starting Home Assistant data fetch and store process...")
    
    # Initialize the Home Assistant client
    hass_client = HassClient()
    
    # Fetch all data from Home Assistant
    data = hass_client.fetch_all_data()
    print(f"Fetched data: {list(data.keys())}")
    
    # Initialize the storage
    storage = Storage()
    
    # Store the current setup
    storage.store_current_setup(data)
    print("Stored current setup in migration/current directory")
    
    print("Process completed successfully")


if __name__ == "__main__":
    main()