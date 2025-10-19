#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LNAmplifier Connection Test Example

This script demonstrates how to connect to LNAmplifier (Low Noise Amplifier) devices, 
display their information, and properly disconnect from the devices.

Usage:
    python LNAmplifierConnectionTest.py

Requirements:
    - LNAmplifier hardware connected to the system
    - Serial communication drivers installed
    - Appropriate serial ports available

History:
    10-18-2025  v1.0.0 - Initial LNAmplifier connection test version
"""

import sys
import os
import asyncio

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.LNAmplifierDriver import LNAmplifier

async def main():
    """Main function to test LNAmplifier device connections."""
    
    # Create LNAmplifier device instance
    device_name = "LNAmplifier"
    device = LNAmplifier(device_name)
    device.debug = False  # Disable debug output for cleaner display
    
    try:
        print("LNAmplifier (Low Noise Amplifier) Connection Test")
        print("=" * 50)
        
        # Open all connected LNAmplifier devices
        print("Searching for and opening LNAmplifier devices...")
        print_status = False
        device.open_all_devices(print_status)
        
        # Check if devices were successfully opened
        if device.port_ok:
            print("✓ Successfully connected to LNAmplifier devices")
            
            # Clear any existing errors
            device.clear_errors()
    
            # Display information for each connected device
            print(f"\nConnected Device Information:")
            print("-" * 35)

            # Get and display device info for each connected device
            for i in range(len(device.serial_ports)):
                print(f"\nDevice {i + 1}:")
                print("-" * 10)
                
                # Display device information
                device.print_device_info(i)
                
                # Show filter setting if available
                try:
                    print(f"Filter Setting: {device._cmdSetFilter}")
                except:
                    print("Filter Setting: Not available")

            print(f"\nTotal Devices Connected: {len(device.serial_ports)}")
            print(f"Debug Mode: {'Enabled' if device.debug else 'Disabled'}")
            
            # Check for any errors
            if device.error != 0:
                print(f"⚠ Device Error: {device.error_description}")
            else:
                print("✓ No device errors detected")            
        else:
            print("✗ Failed to connect to LNAmplifier devices")
            print("\nTroubleshooting checklist:")
            print("  - LNAmplifier hardware is connected and powered")
            print("  - USB/Serial drivers are installed")
            print("  - Correct COM port is available")
            print("  - Device is not in use by another application")
            print("  - Check device model and serial settings")
            
    except Exception as e:
        print(f"✗ Error during device operations: {e}")
        print("\nThis may indicate:")
        print("  - Serial communication issues")
        print("  - Driver compatibility problems")
        print("  - Hardware connection problems")
        
    finally:
        # Always close the device connection
        print("\nClosing device connections...")
        try:
            device.close()
            print("✓ Device connections closed successfully")
        except Exception as e:
            print(f"⚠ Warning during device close: {e}")
        print("\nLNAmplifier connection test completed")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
