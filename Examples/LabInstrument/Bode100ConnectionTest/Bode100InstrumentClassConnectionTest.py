#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bode100 Instrument Class Connection Test

This script demonstrates how to use the Bode100 class from InstrumentDriver.py
to connect to a Bode100 network analyzer. It shows proper initialization,
connection testing, basic configuration, and cleanup using the instrument class.

Usage:
    python Bode100InstrumentClassConnectionTest.py

Requirements:
    - Bode100 network analyzer with SCPI server enabled (see setup instructions below)
    - Network connection to the instrument
    - pyvisa package: pip install pyvisa
    - VISA drivers installed

IMPORTANT SETUP INSTRUCTIONS:
For this script to work, you must first configure the Bode100 SCPI server:
1. Open the Bode100 Analyzer GUI software
2. Click on the "Advanced" tab
3. Find and select the "SCPI Server" option
4. Start the SCPI server
5. Note the IP address and Port numbers displayed in the GUI
6. Update the variables below with the displayed values

History:
    10-17-2025  v1.0.0 - Initial instrument class connection test
"""

import sys
import os

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.InstrumentDriver import Bode100

def main():
    """Main function to test Bode100 instrument class connection."""
    
    # CONFIGURATION: Update these values from your Bode100 GUI
    SCPI_server_IP = '192.168.4.90'  # Replace with IP shown in Bode100 GUI
    SCPI_Port = '5025'               # Replace with Port shown in Bode100 GUI
    
    # Construct VISA resource address for TCPIP socket connection
    visa_address = f'TCPIP::{SCPI_server_IP}::{SCPI_Port}::SOCKET'
    
    # Create Bode100 instance with specific address
    bode = Bode100(model="Bode100", address=visa_address)
    bode.debug = True  # Enable debug output
    
    try:
        print("Bode100 Instrument Class Connection Test")
        print("=" * 50)
        print(f"Target Address: {visa_address}")
        print()
        
        # Test connection using the instrument class
        print("Testing connection to Bode100...")
        connection_successful = bode.check_connection()
        
        if connection_successful:
            print("✓ Bode100 connected successfully!")
            print(f"Device ID: {bode.id}")
            print() 
        else:
            print("✗ ERROR: Could not connect to Bode100!")
            print("\nTroubleshooting checklist:")
            print("  - Verify Bode100 GUI is open")
            print("  - Check that SCPI server is started in Advanced tab")
            print(f"  - Confirm IP address: {SCPI_server_IP}")
            print(f"  - Confirm Port: {SCPI_Port}")
            print("  - Ensure network connectivity")
            print("  - Verify VISA drivers are installed")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error during Bode100 operations: {e}")
        print("\nThis may indicate:")
        print("  - Network connection issues")
        print("  - SCPI server not properly started")
        print("  - Incorrect IP address or port")
        print("  - VISA driver problems")
        sys.exit(1)
        
    finally:
        # Always disconnect properly
        try:
            if bode.is_connected:
                print("\nDisconnecting from Bode100...")
                bode.set_local_mode()  # Return instrument to local control
                bode.close()
                print("✓ Bode100 disconnected successfully")
            print("\nInstrument class connection test completed")
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")

# Run the main function
if __name__ == "__main__":
    main()