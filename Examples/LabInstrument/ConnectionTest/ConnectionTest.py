#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lab Instrument Connection Test Example

This script demonstrates how to connect to laboratory instruments including a 
power supply and digital voltmeter. It configures the power supply, takes a 
voltage measurement with the DVM, and properly disconnects both instruments.

Usage:
    python ConnectionTest.py

Requirements:
    - Compatible laboratory power supply (E36154A or E36233A)
    - Compatible digital voltmeter (34465A)
    - VISA drivers installed
    - Instruments connected via USB or Ethernet
    - DVM connected to power supply output for measurement

History:
    10-14-2025  v1.0.0 - Initial connection test version
    10-14-2025  v1.1.0 - Added DVM support and voltage measurement
"""

import sys
import os

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.InstrumentDriver import PowerSupply, DigitalMultimeter
import time

def main():
    """Main function to test lab power supply and DVM connection."""
    
    # Power supply configuration
    ps_name = "E36233A"  # Can also try "E36154A"
    ps_channel = 1
    target_voltage = 5.0
    current_limit = 1.0
    
    # DVM configuration
    dvm_name = "34465A"
    
    # Create instrument instances
    ps = PowerSupply(model=ps_name)
    dvm = DigitalMultimeter(model=dvm_name)
    ps.debug = False  # Disable debug output
    dvm.debug = False  # Disable debug output
    
    try:
        print("Lab Instrument Connection Test")
        print("=" * 40)
        
        # Search for and connect to power supply
        print("Searching for Power Supply...")
        ps.check_connection()
        
        if ps.is_connected:
            print("✓ Power Supply found and connected successfully!")
            print(f"Device ID: {ps.id}")
            
            # Search for and connect to DVM
            print("\nSearching for Digital Voltmeter...")
            dvm.check_connection()
            
            if dvm.is_connected:
                print("✓ Digital Voltmeter found and connected successfully!")
                print(f"Device ID: {dvm.id}")
                
                # Configure power supply settings
                print(f"\nConfiguring power supply:")
                print(f"  Channel: {ps_channel}")
                print(f"  Voltage: {target_voltage}V")
                print(f"  Current Limit: {current_limit}A")
                
                # Set the power supply parameters
                ps.set_channel(ps_channel)
                ps.set_voltage(target_voltage)
                ps.set_current(current_limit)
                
                # Configure DVM for voltage measurement
                print(f"\nConfiguring DVM for DC voltage measurement...")
                
                # Turn on power supply output
                print("Turning on power supply output...")
                ps.set_output_on()
                print("✓ Power supply output enabled")
                
                # Wait for voltage to settle
                print("Waiting for voltage to settle...")
                time.sleep(0.5)
                
                # Take voltage measurement with DVM
                print(f"\nTaking voltage measurement with DVM...")
                try:
                    measured_voltage = dvm.measure_voltage(ac=False)  # DC voltage measurement
                    print(f"✓ DVM Voltage Measurement: {measured_voltage:.3f}V")
                    print(f"✓ Expected: {target_voltage}V")
                    
                    # Calculate difference
                    voltage_diff = abs(measured_voltage - target_voltage)
                    print(f"✓ Difference: {voltage_diff:.3f}V")
                    
                except Exception as e:
                    print(f"✗ Error taking voltage measurement: {e}")
                
                # Turn off power supply output
                print("\nTurning off power supply output...")
                ps.set_output_off()
                print("✓ Power supply output disabled")
                
                print("✓ Connection test completed successfully")
                
            else:
                print("✗ ERROR: Digital Voltmeter not found!")
                print("  Please check:")
                print("  - DVM is connected via USB or Ethernet")
                print("  - VISA drivers are installed")
                print("  - Device is not in use by another application")
                # Continue with power supply test only
                print("\nContinuing with power supply test only...")
                
                # Configure power supply settings
                print(f"\nConfiguring power supply:")
                print(f"  Channel: {ps_channel}")
                print(f"  Voltage: {target_voltage}V")
                print(f"  Current Limit: {current_limit}A")
                
                ps.set_channel(ps_channel)
                ps.set_voltage(target_voltage)
                ps.set_current(current_limit)
                
                print("✓ Power supply configured successfully")
                print("✓ Power supply connection test completed")
            
        else:
            print("✗ ERROR: Power Supply not found!")
            print("  Please check:")
            print("  - Power supply is connected via USB or Ethernet")
            print("  - VISA drivers are installed")
            print("  - Device is not in use by another application")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error during power supply operations: {e}")
        sys.exit(1)
        
    finally:
        # Always disconnect from both instruments
        print("\nDisconnecting instruments...")
        try:
            if ps.is_connected:
                ps.set_output_off()  # Ensure output is off
                ps.close()
                print("✓ Power supply disconnected successfully")
        except Exception as e:
            print(f"Warning: Error disconnecting power supply: {e}")
            
        try:
            if dvm.is_connected:
                dvm.close()
                print("✓ Digital voltmeter disconnected successfully")
        except Exception as e:
            print(f"Warning: Error disconnecting DVM: {e}")
            
        print("\nConnection test program completed")

# Run the main function
if __name__ == "__main__":
    main()        