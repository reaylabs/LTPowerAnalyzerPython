#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LTPowerAnalyzer Python - LNAmplifier Driver
===========================================

This module provides a Python driver for Low Noise Amplifier (LNAmplifier) control
and automation. The LNAmplifier driver enables programmatic control of amplifier
settings, gain control, and measurement automation for RF/microwave applications.

Features:
    - Serial communication interface for LNAmplifier control
    - Configurable amplifier settings and gain control
    - Filter control and bandwidth management
    - Automated measurement and characterization support
    - Error handling and device status monitoring

Classes:
    LNAmplifier: Main driver class for LNAmplifier device control

Dependencies:
    - SerialDeviceDriver: Base serial communication functionality
    - datetime: Timestamp and logging support
    - math: Mathematical operations for calculations
    - sys: System-specific parameters and functions

Usage Example:
    ```python
    from LNAmplifierDriver import LNAmplifier
    
    # Create LNAmplifier instance
    lna = LNAmplifier(model_name="LNAmplifier_Model", baudrate=9600, timeout=6)
    
    # Connect and configure
    lna.connect("COM3")  # or appropriate port
    lna.set_filter("10")  # Configure filter setting
    
    # Perform operations
    lna.close()
    ```

Author: Analog Devices, Inc.
Date: October 2025
License: See LICENSE.txt in project root
Version: 1.0.0
"""

from SerialDeviceDriver import *
from datetime import datetime
import math
import sys
import struct

class LNAmplifier(SerialDevice): 

    def __init__(self, model_name, baudrate=9600, timeout=6):
        super().__init__(model_name, baudrate, timeout)
        # Basic set commands
        self._cmdSetFilter = "10"
        self._cmdGetFilter = "11"
        self._cmdSetPointCount = "12"
        self._cmdGetPointCount = "13"
        self._cmdSetEEPROMFloatValue = "14"
        self._cmdGetEEPROMFloatValue = "15"
        self._cmdSetEEPROMBaseAddress = "16"
        self._cmdGetEEPROMAddress = "17"
        self._cmdSetEEPROMFloatPage = "18"
        self._cmdGetEEPROMFloatPage = "19"
        self._cmdGetEEPROMDataPageCount = "20"
        self._cmdSetGain = "21"
        self._cmdGetGain = "22"
        self._cmdSetPowerOff = "23"
        self._cmdSetPowerOn = "24"


        #Add error descriptions
        #self.device_errors.add_error_description(5, "Communication Timeout")

    def get_eeprom_address(self, port_index):
        """
        Gets the current EEPROM address.
        
        Args:
            port_index (int): The index of the port to use
            
        Returns:
            int: The current EEPROM address, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the get EEPROM address command
                self.send_command(self._cmdGetEEPROMAddress, port_index)
                
                # Read the address value from the device
                address_value = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Get EEPROM address from port {port_index}: {address_value}")
                
                return address_value
                
            elif self.debug:
                print(f"Get EEPROM Address: Device not ready on port {port_index}")
                return None
                
        except Exception as e:
            print(f"Get EEPROM Address Exception: {e}")
            return None

    def get_eeprom_data_page_count(self, port_index):
        """
        Gets the number of data pages in EEPROM.
        
        Args:
            port_index (int): The index of the port to use
            
        Returns:
            int: The number of data pages in EEPROM, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the get EEPROM data page count command
                self.send_command(self._cmdGetEEPROMDataPageCount, port_index)
                
                # Read the page count value from the device
                page_count = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Get EEPROM data page count from port {port_index}: {page_count}")
                
                return page_count
                
            elif self.debug:
                print(f"Get EEPROM Data Page Count: Device not ready on port {port_index}")
                return None
                
        except Exception as e:
            print(f"Get EEPROM Data Page Count Exception: {e}")
            return None

    def get_eeprom_dataset(self, data_index, port_index):
            """
            Read an array of float values from EEPROM using page-based operations.
            
            This function handles the complete process of reading a dataset:
            1. Reads the current point count from the LNA
            2. Gets the required page count from the LNA  
            3. Sets the EEPROM base address using the data_index
            4. Reads all pages of data using get_eeprom_float_page
            5. Returns an array of point_count float values
            
            Args:
                data_index (int): EEPROM data index (0-8) for base address
                port_index (int): The index of the port to use
                
            Returns:
                list: Array of float values (length = point_count) or None if error
            """
            try:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Get EEPROM Dataset: Device not ready on port {port_index}")
                    return None
                
                # Validate inputs
                if not isinstance(data_index, int) or data_index < 0 or data_index > 8:
                    if self.debug:
                        print(f"Get EEPROM Dataset: Invalid data_index {data_index} (must be 0-8)")
                    return None
                
                # Step 1: Read point count from LNA
                point_count = self.get_point_count(port_index)
                if point_count is None:
                    if self.debug:
                        print("Get EEPROM Dataset: Failed to get point count")
                    return None
                
                point_count = int(point_count) if isinstance(point_count, str) else point_count
                
                if self.debug:
                    print(f"Point count from LNA: {point_count}")
                
                # Step 2: Set EEPROM base address using data_index
                if not self.set_eeprom_base_address(data_index, port_index):
                    if self.debug:
                        print(f"Get EEPROM Dataset: Failed to set base address for data_index {data_index}")
                    return None
                
                # Step 3: Get page count from LNA
                page_count = self.get_eeprom_data_page_count(port_index)
                if page_count is None:
                    if self.debug:
                        print("Get EEPROM Dataset: Failed to get page count")
                    return None
                
                page_count = int(page_count) if isinstance(page_count, str) else page_count
                
                if self.debug:
                    print(f"Page count from LNA: {page_count}")
                
                # Step 4: Read pages of data using get_eeprom_float_page
                dataset = []
                successful_pages = 0
                
                for page_num in range(page_count):
                    # Read the page using get_eeprom_float_page
                    page_data = self.get_eeprom_float_page(port_index)
                    
                    if page_data is not None and len(page_data) == 8:
                        successful_pages += 1
                        
                        # Add values from this page to the dataset
                        for i in range(8):
                            value_index = page_num * 8 + i
                            if value_index < point_count:
                                dataset.append(page_data[i])
                            # Stop adding values once we reach point_count
                        
                        if self.debug:
                            print(f"Page {page_num + 1}/{page_count} read successfully")
                    else:
                        if self.debug:
                            print(f"Failed to read page {page_num + 1}/{page_count}")
                        # Return None if any page fails to read
                        return None
                
                # Verify we got the expected number of values
                if len(dataset) != point_count:
                    if self.debug:
                        print(f"Get EEPROM Dataset: Expected {point_count} values, got {len(dataset)}")
                    return None
                
                if self.debug:
                    print(f"Get EEPROM Dataset: Successfully read {len(dataset)} values from data_index {data_index}")
                
                return dataset
                
            except Exception as e:
                if self.debug:
                    print(f"Get EEPROM Dataset Exception: {e}")
                return None

    def get_eeprom_float_value(self, address, port_index):
        """
        Gets a float value from EEPROM at the specified address.
        
        Args:
            address (int): The EEPROM address to read from
            port_index (int): The index of the port to use
            
        Returns:
            float: The float value from EEPROM, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the get EEPROM float value command
                self.send_command(self._cmdGetEEPROMFloatValue, port_index)
                
                # Send the address
                self.send_value(address, port_index)
                
                # Read the float value from the device
                float_value = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Get EEPROM float value from address {address} on port {port_index}: {float_value}")
                
                return float_value
                
            elif self.debug:
                print(f"Get EEPROM Float Value: Device not ready on port {port_index}")
                return None
                
        except Exception as e:
            print(f"Get EEPROM Float Value Exception: {e}")
            return None

    def get_eeprom_float_page(self, port_index):
        """
        Gets a page of 8 float values from EEPROM.
        The EEPROM address is handled automatically by the device.
        
        Args:
            port_index (int): The index of the port to use
            
        Returns:
            list: List of 8 float values from EEPROM, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the get EEPROM float page command
                self.send_command(self._cmdGetEEPROMFloatPage, port_index)
                
                # Read the comma-delimited string from the device
                response = self.read_value(True, port_index)
                
                if response is None:
                    if self.debug:
                        print(f"Get EEPROM Float Page: No response from port {port_index}")
                    return None
                
                # Parse the comma-delimited string into float values
                try:
                    # Split by comma and convert each to float
                    float_values = [float(val.strip()) for val in response.split(',')]
                    
                    # Validate that we got exactly 8 values
                    if len(float_values) != 8:
                        if self.debug:
                            print(f"Get EEPROM Float Page: Expected 8 values, got {len(float_values)}")
                        return None
                    
                    if self.debug:
                        print(f"Get EEPROM float page from port {port_index}: {float_values}")
                    
                    return float_values
                    
                except (ValueError, AttributeError) as parse_error:
                    if self.debug:
                        print(f"Get EEPROM Float Page: Parse error - {parse_error}")
                    return None
                
            elif self.debug:
                print(f"Get EEPROM Float Page: Device not ready on port {port_index}")
                return None
                
        except Exception as e:
            print(f"Get EEPROM Float Page Exception: {e}")
            return None

    def get_filter(self, port_index):
        """
        Gets the current filter setting from the specified port.
        
        Args:
            port_index (int): The index of the port to query
            
        Returns:
            str: The current filter value, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdGetFilter, port_index)  # Send the read filter command to the specified port
                filter_value = self.read_value(True, port_index)  # Read the filter value
                return filter_value
            elif self.debug:
                print(f"Read Filter Port Not OK")  # Print a debug message if the port is not OK
                return None  # Return None if the port is not valid
        except Exception as e:
            print(f"Read Filter Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    def get_gain(self, port_index):
        """
        Gets the current gain setting from the specified port.
        
        Args:
            port_index (int): The index of the port to query
            
        Returns:
            str: The current gain value (1=60dB, 2=40dB), or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdGetGain, port_index)  # Send the read filter command to the specified port
                gain_value = self.read_value(True, port_index)  # Read the filter value
                return gain_value
            elif self.debug:
                print(f"Read Gain Port Not OK")  # Print a debug message if the port is not OK
                return None  # Return None if the port is not valid
        except Exception as e:
            print(f"Read Gain Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    def get_point_count(self, port_index):
        """
        Gets the current point count setting from the specified port.
        
        Args:
            port_index (int): The index of the port to query
            
        Returns:
            int: The current point count value, or None if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the command to get the point count
                self.send_command(self._cmdGetPointCount, port_index)
                # Read the point count value from the device
                point_count = self.read_value(True, port_index)
                if self.debug:
                    print(f"Point count retrieved from port {port_index}: {point_count}")
                return point_count
            elif self.debug:
                print(f"Get Point Count: Device not ready on port {port_index}")
                return None
        except Exception as e:
            print(f"Get Point Count Exception: {e}")
            return None

    def open_all_devices(self, print_status=True):
        """
        Open all connected LNAmplifier devices. Optionally print device info.
        Exits the program if no devices are found or an exception occurs.

        Args:
            print_status (bool): If True, prints device info and connection status.
        """
        try:
            if print_status:
                print("Searching For LNAmplifier:\n")

            if self.check_connections():
                for i in range(self.port_count):
                    self.port_index = i
                    self.clear_errors()
                    if print_status:
                        self.print_device_info(i)
            else:
                if print_status:
                    print("No LNAmplifier Found.\nExiting program...")
                sys.exit(0)

        except Exception as e:
            print(f"Error opening LNAmplifier devices: {e}")
            sys.exit(0)

    def print_device_info(self, port_index):
        """Prints device information for the specified port index."""
        try:
            if self.port_ok(port_index):
                device_info = self.get_device_info(port_index)
                print(f"Device {port_index + 1} Information:")
                for attr, value in vars(device_info).items():
                    print(f"{attr}: {value}")
            else:
                print(f"Port {port_index} is not valid.")
        except Exception as e:
            print(f"Error retrieving device info for port {port_index}: {e}")

    def set_eeprom_base_address(self, data_index, port_index):
        """
        Sets the base address for EEPROM operations.
        
        Args:
            data_index (int): The data index to set
            port_index (int): The index of the port to use

        Returns:
            bool: True if successful, False if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the set EEPROM base address command
                self.send_command(self._cmdSetEEPROMBaseAddress, port_index)

                # Send the data index
                self.send_value(data_index, port_index)

                # Read the response to confirm the operation
                response = self.read_value(True, port_index)

                if self.debug:
                    print(f"Set EEPROM base address for data index {data_index} on port {port_index}")
                    if response:
                        print(f"Device response: {response}")

                return True

            elif self.debug:
                print(f"Set EEPROM Base Address: Device not ready on port {port_index}")
                return False

        except Exception as e:
            print(f"Set EEPROM Base Address Exception: {e}")
            return False

    def set_eeprom_dataset(self, float_values, data_index, port_index):
        """
        Store an array of float values in EEPROM using page-based operations.
        
        This function handles the complete process of storing a dataset:
        1. Reads the current point count from the LNA
        2. Gets the required page count from the LNA
        3. Sets the EEPROM base address using the data_index
        4. Writes all pages of data using set_eeprom_float_page
        
        Args:
            float_values (list): Array of float values to store
            data_index (int): EEPROM data index (0-8) for base address
            port_index (int): The index of the port to use
            
        Returns:
            bool: True if all data stored successfully, False otherwise
        """
        try:
            if not self.port_ok(port_index):
                if self.debug:
                    print(f"Set EEPROM Dataset: Device not ready on port {port_index}")
                return False
            
            # Validate inputs
            if not isinstance(float_values, list) or len(float_values) == 0:
                if self.debug:
                    print("Set EEPROM Dataset: Invalid float_values array")
                return False
            
            if not isinstance(data_index, int) or data_index < 0 or data_index > 8:
                if self.debug:
                    print(f"Set EEPROM Dataset: Invalid data_index {data_index} (must be 0-8)")
                return False
            
            # Step 1: Read point count from LNA
            point_count = self.get_point_count(port_index)
            if point_count is None:
                if self.debug:
                    print("Set EEPROM Dataset: Failed to get point count")
                return False
            
            point_count = int(point_count) if isinstance(point_count, str) else point_count
            
            if self.debug:
                print(f"Point count from LNA: {point_count}")
            
            # Step 2: Set EEPROM base address using data_index
            if not self.set_eeprom_base_address(data_index, port_index):
                if self.debug:
                    print(f"Set EEPROM Dataset: Failed to set base address for data_index {data_index}")
                return False
            
            # Step 3: Get page count from LNA
            page_count = self.get_eeprom_data_page_count(port_index)
            if page_count is None:
                if self.debug:
                    print("Set EEPROM Dataset: Failed to get page count")
                return False
            
            page_count = int(page_count) if isinstance(page_count, str) else page_count
            
            if self.debug:
                print(f"Page count from LNA: {page_count}")
            
            # Step 4: Write pages of data using set_eeprom_float_page
            successful_pages = 0
            
            for page_num in range(page_count):
                # Prepare 8 float values for this page
                page_values = []
                for i in range(8):
                    value_index = page_num * 8 + i
                    if value_index < len(float_values):
                        page_values.append(float_values[value_index])
                    else:
                        # Pad with zeros if we exceed data count
                        page_values.append(0.0)
                
                # Write the page using set_eeprom_float_page
                if self.set_eeprom_float_page(page_values, port_index):
                    successful_pages += 1
                    if self.debug:
                        print(f"Page {page_num + 1}/{page_count} written successfully")
                else:
                    if self.debug:
                        print(f"Failed to write page {page_num + 1}/{page_count}")
            
            # Check if all pages were written successfully
            success = successful_pages == page_count
            
            if self.debug:
                print(f"Set EEPROM Dataset: {successful_pages}/{page_count} pages written successfully")
                if success:
                    print(f"Dataset stored successfully in data_index {data_index}")
                else:
                    print(f"Dataset storage partially failed ({page_count - successful_pages} pages failed)")
            
            return success
            
        except Exception as e:
            if self.debug:
                print(f"Set EEPROM Dataset Exception: {e}")
            return False

    def set_eeprom_float_page(self, float_values, port_index):
        """
        Sets a page of 8 float values in EEPROM using comma-delimited string.
        The EEPROM address is handled automatically by the device.
        set_eeprom_base_address must be called before writing the first set of values.
        
        Args:
            float_values (list): List of 8 float values to write
            port_index (int): The index of the port to use
            
        Returns:
            bool: True if successful, False if an error occurs
        """
        try:
            # Validate input
            if not isinstance(float_values, (list, tuple)) or len(float_values) != 8:
                if self.debug:
                    print(f"Invalid float_values: must provide exactly 8 float values")
                return False
            
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the set EEPROM float page command
                self.send_command(self._cmdSetEEPROMFloatPage, port_index)
                
                # Convert float values to comma-delimited string
                value_string = ','.join(str(float(val)) for val in float_values)
                
                # Send the comma-delimited string
                self.send_value(value_string, port_index)
                
                # Read the response to confirm the operation
                response = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Set EEPROM float page with 8 values on port {port_index}")
                    print(f"Values: {value_string}")
                    if response:
                        print(f"Device response: {response}")
                
                return True
                
            elif self.debug:
                print(f"Set EEPROM Float Page: Device not ready on port {port_index}")
                return False
                
        except Exception as e:
            print(f"Set EEPROM Float Page Exception: {e}")
            return False

    def set_eeprom_float_value(self, address, float_value, port_index):
        """
        Sets a float value in EEPROM at the specified address.
        
        Args:
            address (int): The EEPROM address to write to
            float_value (float): The float value to store in EEPROM
            port_index (int): The index of the port to use
            
        Returns:
            bool: True if successful, False if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the set EEPROM float value command
                self.send_command(self._cmdSetEEPROMFloatValue, port_index)
                
                # Send the address first
                self.send_value(address, port_index)
                
                # Send the float value second
                self.send_value(float_value, port_index)
                
                # Read the response to confirm the operation
                response = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Set EEPROM float value {float_value} at address {address} on port {port_index}")
                    if response:
                        print(f"Device response: {response}")
                
                return True
                
            elif self.debug:
                print(f"Set EEPROM Float Value: Device not ready on port {port_index}")
                return False
                
        except Exception as e:
            print(f"Set EEPROM Float Value Exception: {e}")
            return False

    def set_filter(self, filter_value,port_index):
        """
        Sets the filter value for the specified port.
        
        Args:
            port_index (int): The index of the port to configure
            filter_value (str): The filter value to set
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetFilter, port_index)  # Send the set filter command to the specified port
                self.send_value(filter_value, port_index)  # Send the filter value
                self.read_value(True, port_index)  # Read the response (ignoring the result)
                if self.debug:
                    print(f"Filter set to {filter_value} on port {port_index}")
            elif self.debug:
                print(f"Set Filter: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Set Filter Exception: {e}")  # Catch and print any exceptions that occur

    def set_gain(self, gain_value,port_index):
        """
        Sets the gain value for the specified port.
        
        Args:
            port_index (int): The index of the port to configure
            gain_value (str): The gain value to set ("1"=60dB, "2"=40dB)
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetGain, port_index)  # Send the set gain command to the specified port
                self.send_value(gain_value, port_index)  # Send the gain value
                self.read_value(True, port_index)  # Read the response (ignoring the result)
                if self.debug:
                    print(f"Gain set to {gain_value} on port {port_index}")
            elif self.debug:
                print(f"Set Gain: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Set Gain Exception: {e}")  # Catch and print any exceptions that occur

    def set_point_count(self, point_count, port_index):
        """
        Sets the point count for the specified port.
        
        Args:
            point_count (int): The point count value to set (must be 51, 101, 201, or 401)
            port_index (int): The index of the port to configure
            
        Returns:
            bool: True if successful, False if an error occurs or invalid point count
        """
        # Valid point count values
        valid_point_counts = [51, 101, 201, 401]
        
        try:
            # Validate the point count value
            if point_count not in valid_point_counts:
                if self.debug:
                    print(f"Invalid point count {point_count}. Must be one of: {valid_point_counts}")
                return False
            
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the set point count command
                self.send_command(self._cmdSetPointCount, port_index)
                
                # Send the point count value
                self.send_value(point_count, port_index)
                
                # Read the response to confirm the operation
                response = self.read_value(True, port_index)
                
                if self.debug:
                    print(f"Set point count to {point_count} on port {port_index}")
                    if response:
                        print(f"Device response: {response}")
                
                return True
                
            elif self.debug:
                print(f"Set Point Count: Device not ready on port {port_index}")
                return False
                
        except Exception as e:
            print(f"Set Point Count Exception: {e}")
            return False

    def set_power_off(self, port_index):
        """
        Turns off all active filters on the board.
        
        Args:
            port_index (int): The index of the port to configure
            
        Returns:
            bool: True if successful, False if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetPowerOff, port_index)  # Send the set filter command
                self.send_value(0, port_index)  # Send filter value 0 to turn off both filters
                response = self.read_value(True, port_index)  # Read the response
                
                if self.debug:
                    print(f"Power offon port {port_index}")
                    if response:
                        print(f"Device response: {response}")
                
                return True
                
            elif self.debug:
                print(f"Set Power Off: Device not ready on port {port_index}")
                return False
                
        except Exception as e:
            print(f"Set Power Off Exception: {e}")
            return False
        
    def set_power_on(self, port_index):
        """
        Turns on all active filters on the board.
        
        Args:
            port_index (int): The index of the port to configure
            
        Returns:
            bool: True if successful, False if an error occurs
        """
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetPowerOn, port_index)  # Send the set filter command
                self.send_value(0, port_index)  # Send filter value 0 to turn off both filters
                response = self.read_value(True, port_index)  # Read the response
                
                if self.debug:
                    print(f"Power offon port {port_index}")
                    if response:
                        print(f"Device response: {response}")
                
                return True
                
            elif self.debug:
                print(f"Set Power Off: Device not ready on port {port_index}")
                return False
                
        except Exception as e:
            print(f"Set Power Off Exception: {e}")
            return False
        
    def set_test_mode(self, port_index, value):
        """Sets the test mode for the specified port to the given boolean value (0 or 1).
           In Test Mode, the automatic system check between commands is disabled."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Convert the boolean value to 0 or 1
                value_to_send = 1 if value else 0
                # Send the command to set the test mode
                self.send_command(self._cmd_set_test_mode, port_index)
                # Send the converted value (0 or 1)
                self.send_value(value_to_send, port_index)
                # Read the response (ignoring the result)
                self.read_value(True, port_index)
            elif self.debug:
                print(f"Set Test Mode: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Set Test Mode Exception: {e}")  # Catch and print any exceptions that occur


  