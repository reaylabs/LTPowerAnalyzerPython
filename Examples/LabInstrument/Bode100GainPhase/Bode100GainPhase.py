#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bode100 Gain and Phase Measurement Example

This script demonstrates how to perform gain and phase measurements using the 
Bode100 network analyzer. It performs a frequency sweep and collects gain 
and phase data for analysis of two-port networks such as filters and amplifiers.

Usage:
    python Bode100GainPhase.py

Requirements:
    - Bode100 network analyzer
    - VISA drivers installed
    - Instrument connected via USB or Ethernet
    - Bode100 software and drivers installed
    - Test device connected between R1 (input) and R2 (output)

History:
    10-17-2025  v1.0.0 - Initial gain/phase measurement example version
"""

import sys
import os
from datetime import datetime

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.InstrumentDriver import Bode100
from Drivers.Utilites import save_data_to_csv

def main():
    """Main function to perform Bode100 gain/phase measurement."""
    
    # CONFIGURATION: Update these values from your Bode100 GUI
    SCPI_server_IP = '192.168.4.90'  # Replace with IP shown in Bode100 GUI
    SCPI_Port = '5025'               # Replace with Port shown in Bode100 GUI
    
    # Construct VISA resource address for TCPIP socket connection
    visa_address = f'TCPIP::{SCPI_server_IP}::{SCPI_Port}::SOCKET'
    
    # Bode100 configuration
    bode_model = "Bode100"  # Generic model name for Bode100
    
    # Measurement parameters
    start_frequency = 10.0      # 10 Hz
    stop_frequency = 1000000.0  # 1 MHzn
    point_count = 401           # 401 points for good resolution
    sweep_type = "LOG"          # Logarithmic sweep
    bandwidth = "3000Hz"        # Measurement bandwidth
    magnitude_dbm = -13.4       # Output signal level in dBm

    # Receiver parameters
    r1_coupling = "AC"          # R1 input coupling (AC/DC)
    r1_impedance = 1000000      # R1 input impedance (1 MΩ)
    r1_attenuation = "0dB"      # R1 attenuation (0dB, 10dB, 20dB, 30dB, 40dB)
    r2_coupling = "AC"          # R2 input coupling (AC/DC)
    r2_impedance = 1000000      # R2 input impedance (1 MΩ)
    r2_attenuation = "30dB"     # R2 attenuation (0dB, 10dB, 20dB, 30dB, 40dB)
    
    # Create Bode100 instance with specific address
    bode = Bode100(model=bode_model, address=visa_address)
    bode.debug = False  # Enable debug output
    
    try:
        print("Bode100 Gain and Phase Measurement")
        print("=" * 40)
        print(f"Target Address: {visa_address}")
        print()
        
        # Test connection to Bode100
        print("Connecting to Bode100 Network Analyzer...")
        connection_successful = bode.check_connection()
        
        if connection_successful:
            print("\n✓ Bode100 found and connected successfully!")
            print(f"Device ID: {bode.id}")
            
            # Configure the sweep parameters
            bode.start_frequency = 10.0
            bode.stop_frequency = 1000000.0
            bode.point_count = 401
            bode.sweep_type = "LOG"
            bode.bandwidth = 3000
            bode.source_level = -13.4
            bode.measurement_type = "GAINphase"
            bode.format = "SLOG"
            bode.attenuator = [0, 30]  # R1=0dB, R2=30dB
            bode.impedance = [1000000, 1000000]  # R1=1MΩ, R2=1MΩ
            bode.trigger_source = "BUS"  # Trigger source set to BUS
            bode.initiate_continuous = True 

            # Write the properties to the instrument
            bode.write_properties()

 
            # Prompt user before executing the sweep
            print("\nA gain/phase measurement sweep is about to be performed.")
            print("Do you want to continue? (y/n): ", end="")
            
            user_response = input().strip().lower()
            
            if user_response != 'y':
                print("Measurement cancelled. Exiting program.")
                sys.exit(0)

            print("Starting measurement...")
            
            # Execute the measurement using the new simplified function
            sweep_result = bode.execute_sweep()
            
            if sweep_result:
                headers, data_rows = sweep_result
                print(f"\n✓ Measurement completed successfully!")
                print(f"✓ Collected {len(data_rows)} data points")
                print(f"✓ Headers: {headers}")
                
                # Convert to the expected format for backward compatibility
                results = []
                for row in data_rows:
                    results.append(tuple(row))
                
                # Display measurement summary
                frequencies = [point[0] for point in results]
                gains = [point[1] for point in results]
                phases = [point[2] for point in results]
                
                print("\nMeasurement Summary:")
                print(f"  Frequency Range: {min(frequencies):.1f} Hz to {max(frequencies):.0f} Hz")
                print(f"  Gain Range: {min(gains):.2f} dB to {max(gains):.2f} dB")
                print(f"  Phase Range: {min(phases):.1f}° to {max(phases):.1f}°")
                
                # Find key measurement points
                max_gain_idx = gains.index(max(gains))
                min_gain_idx = gains.index(min(gains))
                
                print(f"\nKey Measurements:")
                print(f"  Maximum Gain: {gains[max_gain_idx]:.2f} dB at {frequencies[max_gain_idx]:.1f} Hz")
                print(f"  Minimum Gain: {gains[min_gain_idx]:.2f} dB at {frequencies[min_gain_idx]:.1f} Hz")

                # Save data to CSV file
                script_dir = os.path.dirname(os.path.abspath(__file__))
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                csv_filename = f"bode100_gain_phase_{timestamp}.csv"
                full_path = os.path.join(script_dir, csv_filename)
                save_data_to_csv(headers, data_rows, full_path)

                # Display sample data points
                print(f"\nSample Data Points:")
                print("  Frequency (Hz)    Gain (dB)    Phase (°)")
                print("  " + "-" * 40)
                # Display all the data points
                for i in range(len(results)):
                    freq, gain, phase = results[i]
                    print(f"  {freq:12.1f}  {gain:10.2f}  {phase:10.1f}")
                
                print("\n✓ Gain/phase measurement completed successfully")
                
            else:
                print("✗ ERROR: Measurement failed!")
                print("  Please check:")
                print("  - Device connections are secure")
                print("  - Signal levels are appropriate")
                print("  - Instrument calibration is valid")
            
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
            print("\nGain/phase measurement program completed")
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")

# Run the main function
if __name__ == "__main__":
    main()