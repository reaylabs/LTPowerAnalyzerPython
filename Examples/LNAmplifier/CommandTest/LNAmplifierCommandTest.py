#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LNAmplifier Command Test Example

This script demonstrates how to test LNAmplifier (Low Noise Amplifier) device commands
including set_filter and get_filter operations. Only one device is used at a time.

Usage:
    python LNAmplifierCommandTest.py

Requirements:
    - LNAmplifier hardware connected to the system
    - Serial communication drivers installed
    - Appropriate serial ports available

History:
    10-19-2025  v1.0.0 - Initial LNAmplifier command test version
"""

import sys
import os
import asyncio
import time

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.LNAmplifierDriver import LNAmplifier

def test_filter_commands(device, port_index):
    """Test set_filter and get_filter commands."""
    print("\n--- Filter Command Tests ---")
    
    # Test filter values and their expected results
    # Invalid values (-1, 4) should default to "1"
    test_cases = [
        ("-1", "1"),  # Invalid: should default to 1
        ("0", "0"),   # Valid
        ("1", "1"),   # Valid
        ("2", "2"),   # Valid
        ("3", "3"),   # Valid
        ("4", "1")    # Invalid: should default to 1
    ]
    
    for filter_value, expected_result in test_cases:
        try:
            # Test set_filter command
            print(f"Setting filter to {filter_value}...", end=" ")
            device.set_filter(port_index, filter_value)
            
            # Test get_filter command
            current_filter = device.get_filter(port_index)
            
            if current_filter == expected_result:
                if filter_value == expected_result:
                    print("✓ PASS")
                else:
                    print(f"✓ PASS (Defaulted to {expected_result})")
            else:
                print(f"✗ FAIL (Expected: {expected_result}, Got: {current_filter})")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}...")

def test_packet_commands(device, port_index):
    """Test the test_receive_packet command."""
    print("\n--- Packet Command Tests ---")
    
    # Test cases: (data_index, page_index, float_values, description)
    test_cases = [
        (1, 0, [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8], "Data set 1, Page 0"),
        #(2, 0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "Data set 2, Page 0 (all zeros)"),
        #(3, 0, [1.0, -1.0, 2.5, -2.5, 100.0, -100.0, 0.001, -0.001], "Data set 3, Page 0 (mixed values)"),
       # (4, 0, [3.14159, 2.71828, 1.41421, 1.61803, 0.57721, 2.30259, 1.20206, 0.91596], "Data set 4, Page 0 (math constants)")
    ]
    
    for data_index, page_index, float_values, description in test_cases:
        try:
            print(f"Testing {description} (data={data_index}, page={page_index})...", end=" ")
            
            # Send the packet
            response = device.test_receive_packet(data_index, port_index, page_index, float_values)
            
            if response:
                # Parse the response: address_hex,f1,f2,f3,f4,f5,f6,f7,f8
                parts = response.strip().split(',')
                
                if len(parts) == 9:  # 1 address + 8 floats
                    received_addr = int(parts[0], 16)  # Parse hex address from Arduino response
                    received_floats = [float(parts[i]) for i in range(1, 9)]
                    
                    # Note: Arduino response still uses the original address format
                    # We sent page_index,data_index but Arduino reconstructs original address
                    # For now, just check if we got a valid response
                    float_match = all(abs(received_floats[i] - float_values[i]) < 1e-5 
                                    for i in range(8))
                    
                    if float_match:
                        print(f"✓ PASS (Arduino addr: 0x{received_addr:04X})")
                    else:
                        print(f"✗ FAIL (Float mismatch)")
                        print(f"    Expected: {float_values}")
                        print(f"    Received: {received_floats}")
                else:
                    print(f"✗ FAIL (Invalid response format: {len(parts)} parts)")
            else:
                print("✗ FAIL (No response)")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}...")

def test_eeprom_float_commands(device, port_index):
    """Test set_eeprom_float_value and get_eeprom_float_value commands."""
    print("\n--- EEPROM Float Command Tests ---")
    
    # Test address 0 with various float values
    test_address = 0
    test_cases = [
        3.14159,      # Pi
        -2.71828,     # Negative e
        0.0,          # Zero
        123.456,      # Regular positive
        -987.654,     # Regular negative
        1.23e-5,      # Scientific notation small
    ]
    
    for test_value in test_cases:
        try:
            print(f"Testing EEPROM write/read {test_value} at address {test_address}...", end=" ")
            
            # Test set_eeprom_float_value command
            set_result = device.set_eeprom_float_value(test_address, test_value, port_index)
            
            if not set_result:
                print("✗ FAIL (Set operation failed)")
                continue
            
            # Test get_eeprom_float_value command
            read_value = device.get_eeprom_float_value(test_address, port_index)
            
            if read_value is None:
                print("✗ FAIL (Read operation failed)")
                continue
            
            # Compare values with small tolerance for floating point precision
            tolerance = 1e-5
            if isinstance(read_value, str):
                try:
                    read_value = float(read_value)
                except ValueError:
                    print(f"✗ FAIL (Invalid read value: {read_value})")
                    continue
            
            if abs(float(read_value) - test_value) < tolerance:
                print("✓ PASS")
            else:
                print(f"✗ FAIL (Expected: {test_value}, Got: {read_value})")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}...")

def test_eeprom_speed(device, port_index):
    """Test EEPROM write speed by writing 201 float values starting at address 256."""
    print("\n--- EEPROM Speed Test ---")
    
    start_address = 256
    num_values = 201
    address_increment = 4
    
    print(f"Writing {num_values} float values starting at address {start_address}")
    print(f"Address increment: {address_increment} (addresses: {start_address} to {start_address + (num_values-1) * address_increment})")
    
    try:
        # Record start time
        start_time = time.time()
        
        # Write float values to EEPROM
        successful_writes = 0
        for count in range(num_values):
            address = start_address + (count * address_increment)
            float_value = float(count)  # Count as floating point value
            
            # Show progress every 50 writes
            if count % 50 == 0 or count == num_values - 1:
                print(f"Writing value {count} (address {address}, value {float_value})...", end=" ")
            
            # Write the value to EEPROM
            result = device.set_eeprom_float_value(address, float_value, port_index)
            
            if result:
                successful_writes += 1
                if count % 50 == 0 or count == num_values - 1:
                    print("✓")
            else:
                if count % 50 == 0 or count == num_values - 1:
                    print("✗")
                print(f"    ✗ Failed to write at address {address}")
        
        # Record end time
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate write statistics
        if successful_writes > 0:
            avg_time_per_write = total_time / successful_writes
            writes_per_second = successful_writes / total_time
            
            print(f"\n--- Write Speed Results ---")
            print(f"Total writes attempted: {num_values}")
            print(f"Successful writes: {successful_writes}")
            print(f"Failed writes: {num_values - successful_writes}")
            print(f"Write time: {total_time:.3f} seconds")
            print(f"Average time per write: {avg_time_per_write:.4f} seconds")
            print(f"Writes per second: {writes_per_second:.2f}")
            
            if successful_writes == num_values:
                print("✓ All EEPROM writes completed successfully")
            else:
                print(f"⚠ {num_values - successful_writes} writes failed")
                
            # Now test read speed and verify values
            print(f"\n--- Reading back {successful_writes} values for verification ---")
            
            # Record start time for reads
            read_start_time = time.time()
            
            successful_reads = 0
            correct_values = 0
            incorrect_values = 0
            
            # Read back all the values that were successfully written
            for count in range(successful_writes):
                address = start_address + (count * address_increment)
                expected_value = float(count)
                
                # Show progress every 50 reads
                if count % 50 == 0 or count == successful_writes - 1:
                    print(f"Reading value {count} from address {address}...", end=" ")
                
                # Read the value from EEPROM
                read_value = device.get_eeprom_float_value(address, port_index)
                
                if read_value is not None:
                    successful_reads += 1
                    
                    # Convert to float if it's a string
                    if isinstance(read_value, str):
                        try:
                            read_value = float(read_value)
                        except ValueError:
                            if count % 50 == 0 or count == successful_writes - 1:
                                print(f"✗ (Invalid: {read_value})")
                            incorrect_values += 1
                            continue
                    
                    # Check if the value matches (with tolerance for floating point precision)
                    tolerance = 1e-3  # Account for potential 3 decimal place limitation
                    if abs(float(read_value) - expected_value) < tolerance:
                        correct_values += 1
                        if count % 50 == 0 or count == successful_writes - 1:
                            print(f"✓ ({read_value})")
                    else:
                        incorrect_values += 1
                        if count % 50 == 0 or count == successful_writes - 1:
                            print(f"✗ (Expected: {expected_value}, Got: {read_value})")
                else:
                    if count % 50 == 0 or count == successful_writes - 1:
                        print("✗ (Read failed)")
            
            # Record end time for reads
            read_end_time = time.time()
            read_total_time = read_end_time - read_start_time
            
            # Calculate read statistics
            print(f"\n--- Read Speed Results ---")
            print(f"Total reads attempted: {successful_writes}")
            print(f"Successful reads: {successful_reads}")
            print(f"Failed reads: {successful_writes - successful_reads}")
            print(f"Correct values: {correct_values}")
            print(f"Incorrect values: {incorrect_values}")
            print(f"Read time: {read_total_time:.3f} seconds")
            
            if successful_reads > 0:
                avg_time_per_read = read_total_time / successful_reads
                reads_per_second = successful_reads / read_total_time
                print(f"Average time per read: {avg_time_per_read:.4f} seconds")
                print(f"Reads per second: {reads_per_second:.2f}")
                
                # Overall results
                print(f"\n--- Overall Test Results ---")
                print(f"Total test time (write + read): {total_time + read_total_time:.3f} seconds")
                accuracy_percentage = (correct_values / successful_reads * 100) if successful_reads > 0 else 0
                print(f"Data accuracy: {accuracy_percentage:.1f}% ({correct_values}/{successful_reads})")
                
                if correct_values == successful_reads == num_values:
                    print("✓ Perfect test: All values written, read, and verified successfully!")
                elif correct_values == successful_reads:
                    print("✓ All readable values are correct")
                else:
                    print(f"⚠ {incorrect_values} values had mismatches")
            else:
                print("✗ No successful reads completed")
                
        else:
            print("✗ No successful writes completed")
            
    except Exception as e:
        print(f"✗ EEPROM Speed Test Exception: {str(e)}")

def test_point_count_commands(device, port_index):
    """Test set_point_count and get_point_count commands."""
    print("\n--- Point Count Command Tests ---")
    
    # Valid point count values to test
    valid_point_counts = [51, 101, 201, 401]
    
    # Invalid point count values to test
    invalid_point_counts = [50, 100, 150, 200, 300, 500, -1, 0]
    
    print("Testing valid point count values:")
    
    # Test valid point counts
    for point_count in valid_point_counts:
        try:
            print(f"Testing point count {point_count}...", end=" ")
            
            # Test set_point_count command
            set_result = device.set_point_count(point_count, port_index)
            
            if not set_result:
                print("✗ FAIL (Set operation failed)")
                continue
            
            # Test get_point_count command
            read_value = device.get_point_count(port_index)
            
            if read_value is None:
                print("✗ FAIL (Read operation failed)")
                continue
            
            # Convert to int if it's a string
            if isinstance(read_value, str):
                try:
                    read_value = int(read_value)
                except ValueError:
                    print(f"✗ FAIL (Invalid read value: {read_value})")
                    continue
            
            # Check if the value matches
            if int(read_value) == point_count:
                print("✓ PASS")
            else:
                print(f"✗ FAIL (Expected: {point_count}, Got: {read_value})")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}...")
    
    print("\nTesting invalid point count values (should fail):")
    
    # Test invalid point counts - these should fail validation
    for point_count in invalid_point_counts:
        try:
            print(f"Testing invalid point count {point_count}...", end=" ")
            
            # Test set_point_count command - should return False for invalid values
            set_result = device.set_point_count(point_count, port_index)
            
            if not set_result:
                print("✓ PASS (Correctly rejected invalid value)")
            else:
                print("✗ FAIL (Should have rejected invalid value)")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)[:50]}...")
    
    try:
        print(f"\nSetting point count to 201...", end=" ")
        set_result = device.set_point_count(201, port_index)
        
        if set_result:
            final_count = device.get_point_count(port_index)
            if final_count is not None and int(final_count) == 201:
                print("✓ PASS")
            else:
                print(f"✗ FAIL (Expected 201, got {final_count})")
        else:
            print("✗ FAIL")
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)[:50]}...")

async def main():
    """Main function to test LNAmplifier device commands."""
    
    # Create LNAmplifier device instance
    device_name = "LNAmplifier"
    device = LNAmplifier(device_name)
    device.debug = False  # Disable debug output for cleaner display
    
    try:
        print("LNAmplifier Command Test")
        print("=" * 30)
        
        # Open connected LNAmplifier devices
        print("Connecting to LNAmplifier device...")
        device.open_all_devices(print_status=False)
        
        # Check if at least one device was successfully opened
        if device.port_count > 0 and device.port_ok(0):
            print("✓ Device connected successfully")
            
            # Use only the first device (port index 0)
            port_index = 0
            device.clear_errors()
            
            # Show basic device info
            print(f"Using Device 1 (Port {port_index})")
            
            # Run filter command tests
            test_filter_commands(device, port_index)
            
            # Run point count command tests
            test_point_count_commands(device, port_index)
            
            # Run EEPROM float command tests
            test_eeprom_float_commands(device, port_index)
            
            # Run EEPROM speed test
            test_eeprom_speed(device, port_index)
            
            # Check for errors after tests
            if device.error != 0:
                print(f"⚠ Device Error: {device.error_description}")
            else:
                print("\n✓ All tests completed without device errors")
                
        else:
            print("✗ No LNAmplifier device found")
            
    except Exception as e:
        print(f"✗ Test error: {str(e)[:60]}...")
        
    finally:
        # Always close the device connection
        print("\nClosing device connection...")
        try:
            device.close()
            print("✓ Device closed successfully")
        except Exception as e:
            print(f"⚠ Close error: {str(e)[:40]}...")
        print("Test completed")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
