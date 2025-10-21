#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LNAmplifier and Bode100 Calibration Program

This script demonstrates automated calibration by connecting to both the LNAmplifier
and Bode100 network analyzer. It performs the following sequence:
1. Connect to LNAmplifier and configure filter 1
2. Connect to Bode100 and configure for gain-phase measurement
3. Execute 201-point gain-phase sweep
4. Store frequency data in EEPROM data_index_1
5. Store phase data in EEPROM data_index_2

The program uses page-based EEPROM operations for efficient bulk data transfer
and includes comprehensive data validation and error handling.

Usage:
    python LNAmplifierBode100Calibration.py

Requirements:
    - LNAmplifier device connected via serial port
    - Bode100 network analyzer connected via Ethernet/USB
    - VISA drivers installed for Bode100
    - Proper RF connections between devices

History:
    10-20-2025  v1.0.0 - Initial calibration program version
"""

import sys
import os
import time
from datetime import datetime

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.LNAmplifierDriver import LNAmplifier
from Drivers.InstrumentDriver import Bode100
from Drivers.Utilites import save_data_to_csv

def store_data_in_eeprom(lna_device, port_index, data_values, data_index, data_name):
    """
    Store a list of float values in EEPROM using page-based operations.
    
    Args:
        lna_device: LNAmplifier device instance
        port_index: Serial port index for LNAmplifier
        data_values: List of float values to store
        data_index: EEPROM data index (0-3)
        data_name: Description of data being stored (for logging)
    
    Returns:
        bool: True if all data stored successfully, False otherwise
    """
    print(f"\n--- Storing {data_name} in EEPROM Data Index {data_index} ---")
    
    try:
        # Set point count to match our data
        point_count = len(data_values)
        print(f"Setting point count to {point_count}...", end=" ")
        if not lna_device.set_point_count(point_count, port_index):
            print("✗ Failed to set point count")
            return False
        print("✓")
        
        # Set the EEPROM base address for the specified data index
        print(f"Setting EEPROM base address for data index {data_index}...", end=" ")
        if not lna_device.set_eeprom_base_address(data_index, port_index):
            print("✗ Failed to set EEPROM base address")
            return False
        print("✓")
        
        # Get number of pages needed from Arduino
        pages_needed = lna_device.get_eeprom_data_page_count(port_index)
        if pages_needed is None:
            print("✗ Failed to get EEPROM data page count")
            return False
        
        pages_needed = int(pages_needed) if isinstance(pages_needed, str) else pages_needed
        print(f"Pages needed: {pages_needed} (8 floats per page)")
        
        # Record start time
        start_time = time.time()
        
        # Write pages of float values
        successful_pages = 0
        total_floats_written = 0
        
        print(f"Writing {pages_needed} pages of {data_name} data...")
        
        for page_num in range(pages_needed):
            # Prepare 8 float values for this page
            page_values = []
            for i in range(8):
                data_index_in_list = page_num * 8 + i
                if data_index_in_list < len(data_values):
                    page_values.append(data_values[data_index_in_list])
                else:
                    # Pad with zeros if we exceed data count
                    page_values.append(0.0)
            
            # Show progress every 10 pages or for the last page
            if page_num % 10 == 0 or page_num == pages_needed - 1:
                print(f"Writing page {page_num + 1}/{pages_needed}...", end=" ")
            
            # Write the page using set_eeprom_float_page
            result = lna_device.set_eeprom_float_page(page_values, port_index)
            
            if result:
                successful_pages += 1
                total_floats_written += min(8, len(data_values) - page_num * 8)
                if page_num % 10 == 0 or page_num == pages_needed - 1:
                    print("✓")
            else:
                if page_num % 10 == 0 or page_num == pages_needed - 1:
                    print("✗")
                print(f"    ✗ Failed to write page {page_num + 1}")
        
        # Record end time
        end_time = time.time()
        total_time = end_time - start_time
        
        # Report results
        print(f"Storage Results for {data_name}:")
        print(f"  Total pages: {pages_needed}")
        print(f"  Successful pages: {successful_pages}")
        print(f"  Total floats stored: {total_floats_written}")
        print(f"  Storage time: {total_time:.3f} seconds")
        
        if successful_pages == pages_needed:
            print(f"✓ All {data_name} data stored successfully in EEPROM")
            return True
        else:
            print(f"⚠ Only {successful_pages}/{pages_needed} pages stored successfully")
            return False
            
    except Exception as e:
        print(f"✗ Error storing {data_name} data: {e}")
        return False

def verify_eeprom_data(lna_device, port_index, expected_data, data_index, data_name):
    """
    Verify stored EEPROM data by reading it back and comparing with expected values.
    
    Args:
        lna_device: LNAmplifier device instance
        port_index: Serial port index for LNAmplifier
        expected_data: List of expected float values
        data_index: EEPROM data index (0-3)
        data_name: Description of data being verified (for logging)
    
    Returns:
        bool: True if verification successful, False otherwise
    """
    print(f"\n--- Verifying {data_name} in EEPROM Data Index {data_index} ---")
    
    try:
        # Reset base address for reading
        if not lna_device.set_eeprom_base_address(data_index, port_index):
            print("✗ Failed to reset EEPROM base address for reading")
            return False
        
        # Get number of pages to read
        pages_needed = lna_device.get_eeprom_data_page_count(port_index)
        if pages_needed is None:
            print("✗ Failed to get EEPROM data page count")
            return False
        
        pages_needed = int(pages_needed) if isinstance(pages_needed, str) else pages_needed
        
        # Read back all the pages
        successful_reads = 0
        correct_pages = 0
        total_correct_floats = 0
        # Use percentage error tolerance instead of absolute tolerance
        tolerance_percentage = 0.001  # 0.001% tolerance for verification
        
        print(f"Reading {pages_needed} pages for verification...")
        
        for page_num in range(pages_needed):
            if page_num % 10 == 0 or page_num == pages_needed - 1:
                print(f"Reading page {page_num + 1}/{pages_needed}...", end=" ")
            
            # Read the page
            read_page = lna_device.get_eeprom_float_page(port_index)
            
            if read_page is not None and len(read_page) == 8:
                successful_reads += 1
                
                # Compare with expected values
                page_correct = True
                correct_floats_in_page = 0
                
                for i in range(8):
                    data_index_in_list = page_num * 8 + i
                    if data_index_in_list < len(expected_data):
                        expected_value = expected_data[data_index_in_list]
                        read_value = read_page[i]
                        
                        # Calculate percentage error
                        if expected_value != 0:
                            percentage_error = abs((read_value - expected_value) / expected_value) * 100
                            value_matches = percentage_error <= tolerance_percentage
                        else:
                            # For zero values, use small absolute tolerance
                            value_matches = abs(read_value) < 1e-10
                        
                        if value_matches:
                            correct_floats_in_page += 1
                        else:
                            page_correct = False
                            # Debug output for mismatches
                            if expected_value != 0:
                                print(f"\nMismatch at index {data_index_in_list}: expected {expected_value}, got {read_value}, error {percentage_error:.3f}%")
                            else:
                                print(f"\nMismatch at index {data_index_in_list}: expected {expected_value}, got {read_value}")
                    else:
                        # Should be padded with zeros
                        if abs(read_page[i]) < 1e-10:
                            correct_floats_in_page += 1
                        else:
                            page_correct = False
                            print(f"\nPadding error at index {data_index_in_list}: expected 0.0, got {read_page[i]}")
                
                if page_correct:
                    correct_pages += 1
                
                total_correct_floats += correct_floats_in_page
                
                if page_num % 10 == 0 or page_num == pages_needed - 1:
                    print("✓" if page_correct else "✗")
            else:
                if page_num % 10 == 0 or page_num == pages_needed - 1:
                    print("✗ (Read failed)")
        
        # Report verification results
        accuracy_percentage = (correct_pages / successful_reads * 100) if successful_reads > 0 else 0
        print(f"Verification Results for {data_name}:")
        print(f"  Pages verified: {successful_reads}/{pages_needed}")
        print(f"  Correct pages: {correct_pages}")
        print(f"  Page accuracy: {accuracy_percentage:.1f}%")
        print(f"  Total correct floats: {total_correct_floats}")
        
        if correct_pages == pages_needed:
            print(f"✓ {data_name} verification successful")
            return True
        else:
            print(f"⚠ {data_name} verification partial success")
            return False
            
    except Exception as e:
        print(f"✗ Error verifying {data_name} data: {e}")
        return False

def main():
    """Main calibration function."""
    
    # Bode100 SCPI Configuration
    BODE_IP = '192.168.4.90'  # Update with your Bode100 IP
    BODE_PORT = '5025'        # Update with your Bode100 port
 
    print("LNAmplifier Calibration Program With Bode100")
    print("=" * 50)

    # Initialize devices
    lna_device = None
    bode_device = None
    port_index = 0  # Use first available port for LNAmplifier
    point_count = 201  # Number of points for calibration sweep
    
    try:
        # Connect to LNAmplifier using same logic as CommandTest
        print("--- Connecting to LNAmplifier ---\n")
        device_name = "LNAmplifier"
        lna_device = LNAmplifier(device_name)
        lna_device.debug = False  # Set to True for debug output
        lna_device.open_all_devices(print_status=False)
        
        # Check if at least one device was successfully opened
        if lna_device.port_count > 0 and lna_device.port_ok(0):
            print("✓ LNAmplifier connected successfully")
            # Use only the first device (port index 0)
            port_index = 0
            lna_device.clear_errors()
        else:
            print("✗ No LNAmplifier device found")
            return
         
        # Connect to Bode100
        print("\n--- Connecting to Bode100 ---\n")
        visa_address = f'TCPIP::{BODE_IP}::{BODE_PORT}::SOCKET'
        bode_device = Bode100(model="Bode100", address=visa_address)
        bode_device.debug = False  # Set to True for debug output
        if not bode_device.check_connection():
            print("✗ Failed to connect to Bode100")
            return
        print(f"✓ Bode100 {bode_device.id} connected successfully")
        
        # Configure Bode100 for gain-phase measurement
        bode_device.start_frequency = 10.0
        bode_device.stop_frequency = 1000000.0  # 1 MHz
        bode_device.point_count = point_count
        bode_device.sweep_type = "LOG"
        bode_device.bandwidth = 3000
        bode_device.source_level = -13.4
        bode_device.measurement_type = "GAINphase"
        bode_device.format = "SLOG"
        bode_device.attenuator = [0,30]  # R1=0dB, R2=30dB
        bode_device.impedance = [1000000, 1000000]  # R1=1MΩ, R2=1MΩ
        bode_device.trigger_source = "BUS"  # Trigger source set to BUS
        bode_device.initiate_continuous = True

        # Write properties to instrument
        bode_device.write_properties()
        
        # Prompt user before executing measurement
        print(f"\nReady to execute gain-phase measurements for all three filters")
        print("This will:")
        print("  - Measure Filter 1, 2, and 3 sequentially")
        print("  - Store frequency data in EEPROM data_index_0")
        print("  - Store Filter 1 gains in EEPROM data_index_1")
        print("  - Store Filter 2 gains in EEPROM data_index_2")
        print("  - Store Filter 3 gains in EEPROM data_index_3")

        print("\nDo you want to continue? (y/n): ", end="")
        
        user_response = input().strip().lower()
        if user_response != 'y':
            print("Calibration cancelled.")
            return
        
        # Prepare LNAmplifier for measurement
        lna_device.clear_errors()
        lna_device.set_point_count(point_count, port_index)
        
        # Execute measurements for all three filters
        filters_to_measure = [1, 2, 3]
        frequencies = None  # Will be set from first measurement
        all_gains = {}      # Dictionary to store gains for each filter
        all_successes = []  # Track storage success for each filter
        headers = None      # Will be set from first successful measurement
        all_data_rows = []  # Store all measurement data for CSV backup
        
        for filter_num in filters_to_measure:
            print(f"\n--- Measuring Filter {filter_num} ---")
            
            # Set the filter (filter_value as string, then port_index)
            print(f"Setting LNAmplifier to filter {filter_num}...", end=" ")
            lna_device.set_filter(str(filter_num), port_index)
            
            # Verify filter was set correctly
            current_filter = lna_device.get_filter(port_index)
            if current_filter != str(filter_num):
                print(f"✗ Failed to set filter {filter_num} (got {current_filter})")
                continue
            print("✓")
            
            # Execute measurement
            print(f"Executing gain-phase measurement for filter {filter_num}...")
            
            sweep_result = bode_device.execute_sweep()
            
            if not sweep_result:
                print(f"✗ Measurement failed for filter {filter_num}!")
                continue
            
            current_headers, current_data_rows = sweep_result
            print(f"✓ Filter {filter_num} measurement completed successfully!")
            print(f"✓ Collected {len(current_data_rows)} data points")
            
            # Store headers from first successful measurement
            if headers is None:
                headers = current_headers
            
            # Store all data rows for CSV backup
            all_data_rows.extend(current_data_rows)
            
            # Extract data arrays
            current_frequencies = []
            current_gains = []
            current_phases = []
            
            for row in current_data_rows:
                current_frequencies.append(float(row[0]))  # Frequency in Hz
                current_gains.append(float(row[1]))       # Gain in dB
                current_phases.append(float(row[2]))      # Phase in degrees
            
            # Store frequencies only from the first filter
            if frequencies is None:
                frequencies = current_frequencies
                print(f"Frequency data captured: {len(frequencies)} points")
            
            # Store gains for this filter
            all_gains[filter_num] = current_gains
            
            # Display measurement summary for this filter
            print(f"Filter {filter_num} Summary:")
            print(f"  Frequency Range: {min(current_frequencies):.1f} Hz to {max(current_frequencies):.0f} Hz")
            print(f"  Gain Range: {min(current_gains):.2f} dB to {max(current_gains):.2f} dB")
            print(f"  Phase Range: {min(current_phases):.1f}° to {max(current_phases):.1f}°")
        
        # Check if we have any successful measurements
        if frequencies is None or len(all_gains) == 0:
            print("\n✗ No successful measurements to store!")
            print("All filter measurements failed. Please check:")
            print("  - Bode100 connection and configuration")
            print("  - LNAmplifier filter settings")
            print("  - RF signal path connections")
            return
        
        # Store frequency data in EEPROM data_index_0 (only once)
        print("\n" + "="*60)
        print("--- Storing Calibration Data to EEPROM ---")
        freq_success = store_data_in_eeprom(
            lna_device, port_index, frequencies, 
            0, "Frequency Data"
        )
        all_successes.append(freq_success)
        
        # Store gain data for each filter in EEPROM data_index_1, 2, 3
        for i, filter_num in enumerate(filters_to_measure, 1):
            if filter_num in all_gains:
                print("\n" + "="*50)
                gain_success = store_data_in_eeprom(
                    lna_device, port_index, all_gains[filter_num], 
                    i, f"Filter {filter_num} Gain Data"
                )
                all_successes.append(gain_success)
        
        # Verify stored data
        if all(all_successes):
            print("\n" + "="*60)
            print("--- Data Verification ---")
            
            all_verifications = []
            
            # Verify frequency data
            freq_verify = verify_eeprom_data(
                lna_device, port_index, frequencies,
                0, "Frequency Data"
            )
            all_verifications.append(freq_verify)
            
            # Verify gain data for each filter
            for i, filter_num in enumerate(filters_to_measure, 1):
                if filter_num in all_gains:
                    gain_verify = verify_eeprom_data(
                        lna_device, port_index, all_gains[filter_num],
                        i, f"Filter {filter_num} Gain Data"
                    )
                    all_verifications.append(gain_verify)
            
            if all(all_verifications):
                print("\n✓ Calibration completed successfully!")
                print("  - Frequency data stored and verified in data_index_0")
                for i, filter_num in enumerate(filters_to_measure, 1):
                    if filter_num in all_gains:
                        print(f"  - Filter {filter_num} gain data stored and verified in data_index_{i}")
            else:
                print("\n⚠ Calibration completed with verification issues")
        else:
            print("\n⚠ Some data storage operations failed")
        
        # Save measurement data to CSV file for backup
        if headers is not None and len(all_data_rows) > 0:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            csv_filename = f"lna_bode100_calibration_{timestamp}.csv"
            full_path = os.path.join(script_dir, csv_filename)
            save_data_to_csv(headers, all_data_rows, full_path)
            print(f"✓ Measurement data saved to: {csv_filename}")
        else:
            print("⚠ No measurement data to save to CSV")

    except Exception as e:
        print(f"✗ Error during calibration: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up connections
        print("\n--- Cleanup ---")
        
        if bode_device and bode_device.is_connected:
            try:
                print("Disconnecting from Bode100...", end=" ")
                bode_device.set_local_mode()
                bode_device.close()
                print("✓")
            except Exception as e:
                print(f"✗ Error disconnecting Bode100: {e}")
        
        if lna_device and lna_device.port_count > 0:
            try:
                print("Disconnecting from LNAmplifier...", end=" ")
                lna_device.close()
                print("✓")
            except Exception as e:
                print(f"✗ Error disconnecting LNAmplifier: {e}")
        
        print("\nCalibration program completed")

if __name__ == "__main__":
    main()