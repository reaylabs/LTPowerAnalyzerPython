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

class LNAmplifier(SerialDevice): 

    #constructor
    def __init__(self, model_name, baudrate=9600, timeout=6):
        super().__init__(model_name, baudrate, timeout)
        # Basic set commands
        self._cmdSetFilter = "10"

        #Add error descriptions
        #self.device_errors.add_error_description(5, "Communication Timeout")
   

    # Open Devices
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
   
    # Set test mode
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

