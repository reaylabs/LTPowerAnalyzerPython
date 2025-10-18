#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RL2000 Connection Test Example

This script demonstrates how to connect to RL2000 devices, display their 
information, and properly disconnect from the devices.

Usage:
    python RL2000ConnectionTest.py

Requirements:
    - RL2000 hardware connected to the system
    - Serial communication drivers installed
"""

import sys
import os
import asyncio

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.RL2000Driver import RL2000

async def main():
    """Main function to test RL2000 device connections."""
    
    # Create RL2000 device instance
    device_name = "RL2000"
    device = RL2000(device_name)
    device.debug = False  # Disable debug output
    
    try:
        print("RL2000 Connection Test")
        print("=" * 40)
        
        # Open all connected RL2000 devices
        print("Opening all RL2000 devices...")
        print_status = False
        device.open_all_devices(print_status)
        
        # Check if devices were successfully opened
        if device.port_ok:
            print("✓ Successfully connected to RL2000 devices")
            
            # Clear any existing errors
            device.clear_errors()
    
            # Display information for each connected device
            print(f"\nDevice Information:")
            print("-" * 20)

            # Get and display device info for each connected device
            for i in range(len(device.serial_ports)):
                # Display device information header
                device.print_device_info(i)
                temperatures = device.read_temperatures(i)
                print(f"Current Meter: {temperatures[0]}°C, Current Load: {temperatures[1]}°C\n")

            print(f"Debug Mode: {'Enabled' if device.debug else 'Disabled'}")
            
            # Check for any errors
            if device.error != 0:
                print(f"⚠ Device Error: {device.error_description}")
            else:
                print("✓ No device errors detected")
                
        else:
            print("✗ Failed to connect to RL2000 devices")
            print("  Please check:")
            print("  - RL2000 hardware is connected")
            print("  - USB/Serial drivers are installed")
            print("  - Device is not in use by another application")
            
    except Exception as e:
        print(f"✗ Error during device operations: {e}")
        
    finally:
        # Always close the device connection
        print("\nClosing device connections...")
        device.close()
        print("✓ Device connections closed successfully")
        print("\nConnection test completed")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())        