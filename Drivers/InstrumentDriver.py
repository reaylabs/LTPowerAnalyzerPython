#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Instrument Driver Module

This module provides base classes for interfacing with laboratory instruments 
using VISA communication protocol. It includes support for various instrument 
types including power supplies, multimeters, and other test equipment.

Features:
    - VISA-based communication with automatic resource management
    - Device discovery and connection handling
    - Power supply control with voltage/current settings
    - Multimeter measurements (voltage, current, resistance)
    - Configurable timeouts and termination characters
    - Debug mode for development and troubleshooting
    - Error handling and connection status monitoring

Classes:
    - Instrument: Base instrument class with VISA communication
    - PowerSupply: Specialized class for power supply control
    - Multimeter: Specialized class for measurement instruments

Requirements:
    - pyvisa package: pip install pyvisa
    - VISA backend (NI-VISA or compatible)
    - Compatible laboratory instruments with VISA support

Author: Analog Devices, Inc.
License: See LICENSE.txt

History:
    11-29-2024  v1.0.0 - Initial version
    10-13-2025  v1.0.1 - Updated header and documentation
"""

import pyvisa
import math
import os

class Instrument:
    def __init__(self, model: str, address: str = None, debug: bool = False):
        """
        Initialize the instrument with the given address.
        
        :param address: The VISA resource address of the instrument (e.g., "USB0::0x1234::0x5678::INSTR").
        :param debug: If True, enables debug messages.
        """
        self._address = address
        self._model = model
        self._debug = debug
        self._rm = pyvisa.ResourceManager()
        self._instrument = None
        self._is_connected = False
        self._read_termination = None
        self._write_termination = '\r\n'
        self._timeout = 2000
        self._discover_timeout = 500


    #create address property
    @property
    def address(self) -> str:
        """
        Retuns the VISA resource address of the instrument.
        """
        return self._address

    @property
    def is_connected(self) -> bool:
        """
        Returns whether the instrument is connected.
        """
        return self._is_connected

    @property
    def debug(self) -> bool:
        """
        Get the debug state.
        """
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        """
        Set the debug state.
        
        :param value: Boolean to enable or disable debug messages.
        """
        self._debug = value
    
    @property
    def id(self) -> str:
        """
        Queries the instrument's identification string.

        :return: The identification string of the instrument.
        :raises: RuntimeError if the instrument is not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        return self._instrument.query("*IDN?")

    def check_connection(self) -> bool:
        """
        Check if the instrument is reachable and update the connection status.
        
        :return: True if the connection is successful, False otherwise.
        """
        response = None
        if self._address is None:
            resources = self._rm.list_resources()  
        else:
            resources = [self._address]
        
        # search through all resources to find the one that matches the model
        for resource in resources:
            try:
                instrument = self._rm.open_resource(resource)
                instrument.read_termination = self._read_termination
                instrument.write_termination = self._write_termination
                
                instrument.timeout = self._discover_timeout
                response = instrument.query("*IDN?")
                if self._model in response:
                    self._address = resource
                    instrument.timeout = self._timeout
                    self._instrument = instrument
                    self._is_connected = True                 
                    break
                else:
                    if (self.address != None):
                        self._instrument = self._rm.open_resource(self._address)
                        self._instrument.read_termination = self._read_termination
                        self._instrument.write_termination = self._write_termination
                        self._instrument.timeout = self._timeout

                        # Perform a simple query to verify the connection
                        response = self._instrument.query("*IDN?")
                        self._is_connected = True

            except pyvisa.VisaIOError as e:
                if self.debug:
                    print(f"Connection error: {e}")
                self._is_connected = False
        
        if self.debug:
            if self._is_connected:
                print(f"ID: {response}")
            else:
                print(f"Failed to connect to: {self._model}")
        return self._is_connected

    def reset(self):
        """
        Sends the reset command (*RST) to the instrument.
        
        :raises: RuntimeError if the instrument is not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        try:
            self._instrument.write("*RST")
            if self.debug:
                print(f"Instrument at {self._address} has been reset.")
        except pyvisa.VisaIOError as e:
            print(f"Failed to reset the instrument: {e}")

    def set_local_mode(self):
        """
        Put the device back into local mode, allowing manual operation.

        :raises: RuntimeError if the instrument is not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        try:
            self._instrument.write("SYST:LOC")
            if self.debug:
                print(f"Instrument at {self._address} is now in local mode.")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set the instrument to local mode: {e}")

    def close(self):
        """
        Closes the connection to the instrument if it is open.
        """
        if hasattr(self, '_instrument') and self._instrument:
            try:
                self._instrument.close()
                if hasattr(self, '_debug') and self._debug:
                    print(f"Connection to {self._address} closed.")
            except pyvisa.VisaIOError as e:
                print(f"Failed to close the connection: {e}")
            finally:
                self._instrument = None
        if hasattr(self, '_is_connected'):
            self._is_connected = False

    def __del__(self):
        """
        Ensures the connection is closed when the object is deleted.
        """
        self.close()

class DigitalMultimeter(Instrument):
    def __init__(self, model: str, address: str = None, debug: bool = False):
        super().__init__(model, address, debug)

    def measure_voltage(self, ac: bool = False) -> float:
        """
        Measures voltage (AC or DC).

        :param ac: If True, measures AC voltage. Otherwise, measures DC voltage.
        :return: The measured voltage value.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        mode = "AC" if ac else "DC"
        command = f"MEAS:VOLT:{mode}?"
        try:
            result = self._instrument.query(command)
            return float(result)
        except pyvisa.VisaIOError as e:
            print(f"Failed to measure voltage: {e}")
            return float('nan')

    def measure_current(self, ac: bool = False) -> float:
        """
        Measures current (AC or DC).

        :param ac: If True, measures AC current. Otherwise, measures DC current.
        :return: The measured current value.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        mode = "AC" if ac else "DC"
        command = f"MEAS:CURR:{mode}?"
        try:
            result = self._instrument.query(command)
            return float(result)
        except pyvisa.VisaIOError as e:
            print(f"Failed to measure current: {e}")
            return float('nan')

    def measure_resistance(self) -> float:
        """
        Measures resistance.

        :return: The measured resistance value.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        command = "MEAS:RES?"
        try:
            result = self._instrument.query(command)
            return float(result)
        except pyvisa.VisaIOError as e:
            print(f"Failed to measure resistance: {e}")
            return float('nan')

    def setup_3a_current_measurement(self):
        """
        Configures the instrument for 3A DC current measurement.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        try:
            self._instrument.write("CONF:CURR:DC")
            self._instrument.write("SENS:CURR:DC:TERM 3")
            self._instrument.write("SENS:CURR:DC:RANG:AUTO ON")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set up 3A current measurement: {e}")

    def setup_10a_current_measurement(self):
        """
        Configures the instrument for 10A DC current measurement.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        try:
            self._instrument.write("CONF:CURR:DC")
            self._instrument.write("SENS:CURR:DC:TERM 10")
            self._instrument.write("SENS:CURR:DC:RANG:AUTO ON")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set up 10A current measurement: {e}")

    def setup_resistance_measurement(self):
        """
        Configures the instrument for resistance measurement.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        try:
            self._instrument.write("CONF:RES")
            self._instrument.write("SENS:RES:RANG:AUTO ON")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set up resistance measurement: {e}")

    def setup_voltage_measurement(self, ac: bool = False):
        """
        Configures the instrument for voltage measurement (AC or DC).

        :param ac: If True, configures for AC voltage. Otherwise, configures for DC voltage.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        mode = "AC" if ac else "DC"
        try:
            self._instrument.write(f"CONF:VOLT:{mode}")
            self._instrument.write(f"SENS:VOLT:{mode}:RANG:AUTO ON")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set up voltage measurement: {e}")

class Bode100(Instrument):


    def __init__(self, model: str, address: str = None, debug: bool = False):
        """
        Initializes the Bode100 instrument.

        :param model: Model of the instrument.
        :param address: VISA address of the instrument.
        :param debug: Enables debug mode if True.
        """
        super().__init__(model, address, debug)
        self._read_termination = '\n'
        self._write_termination = '\n'
        self._attenuator = [0, 30]  # Default values: [Ch1, Ch2] in dB
        self._bandwidth = 300  # Default value in Hz
        self._format = "SLOG"  # Default value (logarithmic magnitude + phase)
        self._impedance = [50, 50]  # Default values: [Ch1, Ch2] in ohms
        self._initiate_continuous = True  # Default value (ON - continuous initiation activated)
        self._measurement_type = "GAINphase"  # Default value (gain-phase measurement)
        self._start_frequency = 10  # Default value in Hz
        self._source_level = -10  # Default value in dBm
        self._stop_frequency = 1e6  # Default value in Hz (1 MHz)
        self._point_count = 201  # Default value
        self._sweep_type = "LOG"  # Default value (LOG or LIN)
        self._trigger_source = "INT"  # Default value (Internal trigger)
        self._z_type = "Z"  # Default value (impedance)
        
    @property
    def attenuator(self):
        """
        Get the attenuator values for both channels.
        
        Returns:
            list: List of two attenuator values [Ch1_dB, Ch2_dB]
        """
        return self._attenuator.copy()  # Return a copy to prevent external modification
    
    @attenuator.setter
    def attenuator(self, value):
        """
        Set the attenuator values for both channels.
        
        Args:
            value (list): List of two attenuator values [Ch1_dB, Ch2_dB]
                         Each value must be one of [0, 10, 20, 30, 40] dB
        """
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Attenuator must be a list or tuple with exactly 2 values [Ch1, Ch2]")
        
        allowed_values = [0, 10, 20, 30, 40]
        for i, val in enumerate(value):
            if val not in allowed_values:
                raise ValueError(f"Attenuator Ch{i+1} must be one of {allowed_values}, got {val}")
        
        self._attenuator = list(value)
        
    @property
    def bandwidth(self):
        """
        Get the receiver bandwidth for measurements.
        
        Returns:
            int: Receiver bandwidth in Hz
        """
        return self._bandwidth
    
    @bandwidth.setter
    def bandwidth(self, value):
        """
        Set the receiver bandwidth for measurements.
        
        Args:
            value (int): Receiver bandwidth in Hz (must be one of the allowed values)
        """
        allowed_values = [1, 3, 10, 30, 100, 300, 1000, 3000]
        if value not in allowed_values:
            raise ValueError(f"Bandwidth must be one of {allowed_values}, got {value}")
        self._bandwidth = value
        
    @property
    def impedance(self):
        """
        Get the input impedance values for both channels.
        
        Returns:
            list: List of two impedance values [Ch1_ohms, Ch2_ohms]
        """
        return self._impedance.copy()  # Return a copy to prevent external modification
    
    @impedance.setter
    def impedance(self, value):
        """
        Set the input impedance values for both channels.
        
        Args:
            value (list): List of two impedance values [Ch1_ohms, Ch2_ohms]
                         Each value must be either 50 or 1e6 ohms
        """
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Impedance must be a list or tuple with exactly 2 values [Ch1, Ch2]")
        
        allowed_values = [50, 1e6]
        for i, val in enumerate(value):
            if val not in allowed_values:
                raise ValueError(f"Impedance Ch{i+1} must be one of {allowed_values}, got {val}")
        
        self._impedance = list(value)
        
    @property
    def initiate_continuous(self):
        """
        Get the continuous initiation mode status.
        
        Returns:
            bool: True if continuous initiation is ON, False if OFF
        """
        return self._initiate_continuous
    
    @initiate_continuous.setter
    def initiate_continuous(self, value):
        """
        Set the continuous initiation mode.
        
        Args:
            value (bool or int or str): Continuous initiation mode
                                       Accepts: True/False, 1/0, "ON"/"OFF"
        """
        # Convert various input formats to boolean
        if isinstance(value, bool):
            self._initiate_continuous = value
        elif isinstance(value, int):
            if value in [0, 1]:
                self._initiate_continuous = bool(value)
            else:
                raise ValueError("Integer value must be 0 (OFF) or 1 (ON)")
        elif isinstance(value, str):
            value_upper = value.upper()
            if value_upper in ["ON", "1"]:
                self._initiate_continuous = True
            elif value_upper in ["OFF", "0"]:
                self._initiate_continuous = False
            else:
                raise ValueError("String value must be 'ON', 'OFF', '1', or '0'")
        else:
            raise ValueError("Value must be bool, int (0/1), or str ('ON'/'OFF')")
        
    @property
    def format(self):
        """
        Get the data format for measurements.
        
        Returns:
            str: Data format code
        """
        return self._format
    
    @format.setter
    def format(self, value):
        """
        Set the data format for measurements.
        
        Args:
            value (str): Data format code (must be one of the allowed values)
        """
        allowed_values = [
            "GDEL",     # group delay
            "IMAG",     # imaginary part
            "MLIN",     # linear magnitude
            "MLOG",     # logarithmic magnitude
            "PHAS",     # phase (in degrees)
            "REAL",     # real part
            "SWR",      # standing wave ratio
            "UPHA",     # unwrapped phase
            "SLIN",     # linear magnitude + phase (deg)
            "SLOG",     # logarithmic magnitude + phase (deg)
            "SCOM",     # real part + imaginary part
            "SMIT",     # R + jX - (resistance + reactance)
            "SADM"      # G + jB - (conductance + susceptance)
        ]
        if value not in allowed_values:
            raise ValueError(f"Format must be one of {allowed_values}, got '{value}'")
        self._format = value
        
    @property
    def measurement_type(self):
        """
        Get the measurement type.
        
        Returns:
            str: Measurement type code
        """
        return self._measurement_type
    
    @measurement_type.setter
    def measurement_type(self, value):
        """
        Set the measurement type.
        
        Args:
            value (str): Measurement type code (must be one of the allowed values)
        """
        allowed_values = [
            "CH1",       # Absolute measurement on channel 1 (VRMS)
            "CH2",       # Absolute measurement on channel 2 (VRMS)
            "GAINphase", # Gain - phase measurement
            "R",         # Absolute measurement on channel R (Ch1) (VRMS)
            "S11",       # S11 measurement
            "S21",       # S21 measurement
            "T",         # Absolute measurement on channel T (Ch2) (VRMS)
            "Z"          # Impedance measurement
        ]
        if value not in allowed_values:
            raise ValueError(f"Measurement type must be one of {allowed_values}, got '{value}'")
        self._measurement_type = value
        
    @property
    def point_count(self):
        """
        Get the number of measurement points for sweeps.
        
        Returns:
            int: Number of measurement points
        """
        return self._point_count
    
    @point_count.setter
    def point_count(self, value):
        """
        Set the number of measurement points for sweeps.
        
        Args:
            value (int): Number of measurement points (must be one of the allowed values)
        """
        allowed_values = [51, 101, 201, 401, 801, 1601, 2048, 3201, 4096, 6401, 12801, 16501]
        if value not in allowed_values:
            raise ValueError(f"Point count must be one of {allowed_values}, got {value}")
        self._point_count = value
        
    @property
    def start_frequency(self):
        """
        Get the start frequency for measurements.
        
        Returns:
            float: Start frequency in Hz
        """
        return self._start_frequency
    
    @start_frequency.setter
    def start_frequency(self, value):
        """
        Set the start frequency for measurements.
        
        Args:
            value (float): Start frequency in Hz (must be between 1 and 50e6 Hz)
        """
        if value < 1 or value > 50e6:
            raise ValueError("Start frequency must be between 1 and 50e6 Hz")
        self._start_frequency = value
        
    @property
    def source_level(self):
        """
        Get the source level for measurements.
        
        Returns:
            float: Source level in dBm
        """
        return self._source_level
    
    @source_level.setter
    def source_level(self, value):
        """
        Set the source level for measurements.
        
        Args:
            value (float): Source level in dBm (must be between -30 and 13 dBm)
        """
        if value < -30 or value > 13:
            raise ValueError("Source level must be between -30 and 13 dBm")
        self._source_level = value
        
    @property
    def stop_frequency(self):
        """
        Get the stop frequency for measurements.
        
        Returns:
            float: Stop frequency in Hz
        """
        return self._stop_frequency
    
    @stop_frequency.setter
    def stop_frequency(self, value):
        """
        Set the stop frequency for measurements.
        
        Args:
            value (float): Stop frequency in Hz (must be between 1 and 50e6 Hz)
        """
        if value < 1 or value > 50e6:
            raise ValueError("Stop frequency must be between 1 and 50e6 Hz")
        if hasattr(self, '_start_frequency') and value <= self._start_frequency:
            raise ValueError("Stop frequency must be greater than start frequency")
        self._stop_frequency = value
        
    @property
    def sweep_type(self):
        """
        Get the sweep type for measurements.
        
        Returns:
            str: Sweep type ("LIN" for linear, "LOG" for logarithmic)
        """
        return self._sweep_type
    
    @sweep_type.setter
    def sweep_type(self, value):
        """
        Set the sweep type for measurements.
        
        Args:
            value (str): Sweep type (must be either "LIN" or "LOG")
        """
        allowed_values = ["LIN", "LOG"]
        if value not in allowed_values:
            raise ValueError(f"Sweep type must be one of {allowed_values}, got '{value}'")
        self._sweep_type = value
        
    @property
    def trigger_source(self):
        """
        Get the trigger source for measurements.
        
        Returns:
            str: Trigger source code
        """
        return self._trigger_source
    
    @trigger_source.setter
    def trigger_source(self, value):
        """
        Set the trigger source for measurements.
        
        Args:
            value (str): Trigger source code (must be one of the allowed values)
        """
        allowed_values = [
            "BUS",  # BUS trigger - can be triggered with *TRG or :TRIG:SING
            "INT",  # Internal trigger - device triggers itself (continuous)
            "EXT"   # External trigger - depends on device availability
        ]
        if value not in allowed_values:
            raise ValueError(f"Trigger source must be one of {allowed_values}, got '{value}'")
        self._trigger_source = value
        
    @property
    def z_type(self):
        """
        Get the impedance measurement type.
        
        Returns:
            str: Impedance measurement type code
        """
        return self._z_type
    
    @z_type.setter
    def z_type(self, value):
        """
        Set the impedance measurement type.
        
        Args:
            value (str): Impedance measurement type code (must be one of the allowed values)
        """
        allowed_values = [
            "Cp",   # parallel capacitance
            "Cs",   # serial capacitance
            "D",    # dissipation factor (tan delta)
            "Lp",   # parallel inductance
            "Ls",   # serial inductance
            "QTg",  # quality factor calculated based on group delay time (Tg)
            "Q",    # quality factor
            "Rp",   # parallel resistance
            "Rs",   # serial resistance
            "Y",    # admittance
            "Z"     # impedance
        ]
        if value not in allowed_values:
            raise ValueError(f"Z-type must be one of {allowed_values}, got '{value}'")
        self._z_type = value
        
    def write_properties(self):
        """
        Write all property values to the Bode100 instrument using SCPI commands.
        This configures the instrument with the current property settings.
        """
        try:
            # Set measurement type (MUST be first - resets other properties)
            self._instrument.write(f':CALC:PAR:DEF {self._measurement_type}')
            
            # Set input attenuators
            self._instrument.write(f':INP:ATT:CH1 {self._attenuator[0]}')
            self._instrument.write(f':INP:ATT:CH2 {self._attenuator[1]}')
            
            # Set receiver bandwidth
            self._instrument.write(f':SENS:BAND {self._bandwidth}')
            
            # Set data format
            self._instrument.write(f':CALC:FORM {self._format}')
            
            # Set input impedances
            self._instrument.write(f':INP:IMP:CH1 {int(self._impedance[0])}')
            self._instrument.write(f':INP:IMP:CH2 {int(self._impedance[1])}')
            
            # Set continuous initiation mode
            self._instrument.write(f':INIT:CONT {1 if self._initiate_continuous else 0}')
            
            # Set number of measurement points
            self._instrument.write(f':SENS:SWE:POIN {self._point_count}')
            
            # Set start frequency
            self._instrument.write(f':SENS:FREQ:STAR {self._start_frequency}')
            
            # Set source level
            self._instrument.write(f':SOUR:POW {self._source_level}')
            
            # Set stop frequency
            self._instrument.write(f':SENS:FREQ:STOP {self._stop_frequency}')
            
            # Set sweep type
            self._instrument.write(f':SENS:SWE:TYPE {self._sweep_type}')
            
            # Set trigger source
            self._instrument.write(f':TRIG:SOUR {self._trigger_source}')
            
            # Set impedance measurement type (Z-type)
            self._instrument.write(f':SENS:Z:TYPE {self._z_type}')
            
            # Wait for all commands to complete
            self._instrument.write('*WAI')
            
            if self.debug:
                print("Properties written to Bode100:")
                print(f"  Attenuator Ch1: {self._attenuator[0]} dB")
                print(f"  Attenuator Ch2: {self._attenuator[1]} dB")
                print(f"  Bandwidth: {self._bandwidth} Hz")
                print(f"  Format: {self._format}")
                print(f"  Impedance Ch1: {int(self._impedance[0])} ohms")
                print(f"  Impedance Ch2: {int(self._impedance[1])} ohms")
                print(f"  Initiate Continuous: {'ON' if self._initiate_continuous else 'OFF'}")
                print(f"  Measurement type: {self._measurement_type}")
                print(f"  Point count: {self._point_count}")
                print(f"  Start frequency: {self._start_frequency} Hz")
                print(f"  Source level: {self._source_level} dBm")
                print(f"  Stop frequency: {self._stop_frequency} Hz")
                print(f"  Sweep type: {self._sweep_type}")
                print(f"  Trigger source: {self._trigger_source}")
                print(f"  Z-type: {self._z_type}")
                
        except Exception as e:
            print(f"Error writing properties to Bode100: {e}")
            raise
        

    def read_measurement_data(self):
        """
        Reads the measurement data from the Bode100 instrument.

        Returns:
            list: List of measurement data points as floats.
        """
        if not self.is_connected:
            print("✗ ERROR: Instrument not connected. Cannot read measurement data.")
            return []
        
        try:
            frequency_response = self._instrument.query(":SENS:FREQ:DATA?")
            frequency_list = [float(x) for x in frequency_response.split(',')]
            
            # Read measurement data (combined magnitude and phase)
            measurement_response = self._instrument.query(":CALC:DATA:SDAT?")
            measurement_list = [float(x) for x in measurement_response.split(',')]
            return frequency_list, measurement_list

        except Exception as e:
            print(f"Error reading measurement data from Bode100: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return []
        
    def read_properties(self):
        """
        Read property values from the Bode100 instrument and update internal properties.
        Only reads properties that are known to be supported by the Bode100 SCPI interface.
        """
        if not self.is_connected:
            print("✗ ERROR: Instrument not connected. Cannot read properties.")
            return False
        
        try:
            # Read basic sweep configuration (known to work)
            start_freq = self._instrument.query(":SENS:FREQ:STAR?").strip()
            self._start_frequency = float(start_freq)
            
            stop_freq = self._instrument.query(":SENS:FREQ:STOP?").strip()
            self._stop_frequency = float(stop_freq)
            
            points = self._instrument.query(":SENS:SWE:POIN?").strip()
            self._point_count = int(points)
            
            sweep_type = self._instrument.query(":SENS:SWE:TYPE?").strip()
            # Convert response to our format (instrument may return "LIN" or "LINEAR")
            if "LIN" in sweep_type.upper():
                self._sweep_type = "LIN"
            elif "LOG" in sweep_type.upper():
                self._sweep_type = "LOG"
            else:
                self._sweep_type = sweep_type  # Keep original if unrecognized
            
            bandwidth = self._instrument.query(":SENS:BAND?").strip()
            self._bandwidth = int(float(bandwidth))  # Convert to int Hz
            
            # Try to read format (may not be supported on all firmware versions)
            try:
                format_resp = self._instrument.query(":CALC:FORM?").strip()
                self._format = format_resp
            except:
                if self.debug:
                    print("  Note: Format query not supported, keeping current value")
            
            # Try to read source level
            try:
                source_level = self._instrument.query(":SOUR:VOLT?").strip()
                self._source_level = float(source_level)
            except:
                if self.debug:
                    print("  Note: Source level query not supported, keeping current value")
            
            # Try to read trigger source
            try:
                trigger_source = self._instrument.query(":TRIG:SOUR?").strip()
                self._trigger_source = trigger_source
            except:
                if self.debug:
                    print("  Note: Trigger source query not supported, keeping current value")
            
            # Try to read continuous initiation mode
            try:
                init_cont = self._instrument.query(":INIT:CONT?").strip()
                # Convert response to boolean (may return "1"/"0" or "ON"/"OFF")
                self._initiate_continuous = init_cont.upper() in ["1", "ON", "TRUE"]
            except:
                if self.debug:
                    print("  Note: Initiate continuous query not supported, keeping current value")
            
            # Note: The following properties cannot be reliably read from Bode100:
            # - attenuator: :INP:ATT:CH1? and :INP:ATT:CH2? not consistently supported
            # - impedance: :INP:IMP:CH1? and :INP:IMP:CH2? not consistently supported  
            # - initiate_continuous: :INIT:CONT? may not be consistently supported
            # - measurement_type: :CALC:PAR:DEF? response format varies
            # - trigger_source: :TRIG:SOUR? may not be consistently supported
            # - z_type: :SENS:Z:TYPE? not consistently supported
            
            if self.debug:
                print("Properties read from Bode100:")
                print(f"  Start frequency: {self._start_frequency} Hz")
                print(f"  Stop frequency: {self._stop_frequency} Hz")
                print(f"  Point count: {self._point_count}")
                print(f"  Sweep type: {self._sweep_type}")
                print(f"  Bandwidth: {self._bandwidth} Hz")
                print(f"  Format: {self._format}")
                print(f"  Initiate Continuous: {'ON' if self._initiate_continuous else 'OFF'}")
                print(f"  Source level: {self._source_level} dBm")
                print(f"  Trigger source: {self._trigger_source}")
                print("  Note: Some properties (attenuator, impedance, etc.) cannot be reliably read")
            
            return True
            
        except Exception as e:
            print(f"Error reading properties from Bode100: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
        
    def read_calibration_file(self, filename):
        """
        Reads and loads a calibration file into the instrument.

        Parameters:
            filename (str): Name of the calibration file to be loaded.
        """
        try:
            #Set the instrument parameter definition to impedance
            self._instrument.write(':CALC:PAR:DEF Z') 
            print("Setting parameter to Z: ", self._instrument.query('*OPC?'))  # Check operation complete

            # Construct the absolute file path and send the load command
            absolute_filename = os.path.join(os.getcwd(), filename)
            command = f':MEM:LOAD:CORR:FULL {filename}'
            self._instrument.write(command)
            print("Loading calibration file: ", self._instrument.query('*OPC?'))  # Check operation complete

            #Enable full correction mode
            self._instrument.write(":SENS:CORR:FULL:ENAB 1")
            print("Enabling full correction: ", self._instrument.query('*OPC?'))  # Check operation complete

            #Query if correction mode is active
            active = self._instrument.query(":SENS:CORR:FULL:ENAB?")
            print(f"Full correction enabled status: {active}")

        except Exception as e:
            #Handle errors during the calibration process
            print(f"Error loading calibration file: {e}")

    def calibrate_open(self):
        try:
            self._instrument.write(':CALC:PAR:DEF Z')
            self._instrument.write(':SENS:Z:METH TSER')
            self._instrument.write(':SENS:CORR:FULL:OPEN:EXEC')
            self._instrument.write('*WAI')
        except Exception as e:
            print(f"Error execting short calibration : {e}")

    def calibrate_short(self):
        try:
            self._instrument.write(':CALC:PAR:DEF Z')
            self._instrument.write(':SENS:Z:METH TSER')
            self._instrument.write(':SENS:CORR:FULL:SHORT:EXEC')
            self._instrument.write('*WAI')
        except Exception as e:
            print(f"Error execting short calibration : {e}")

    def calibrate_load(self):
        try:
            self._instrument.write(":CALC:PAR:DEF Z")
            self._instrument.write(":SENS:Z:METH TSER")
            self._instrument.write(":SENS:CORR:FULL:LOAD:EXEC")
            self._instrument.write("*WAI")
        except Exception as e:
            print(f"Error execting load calibration : {e}")
    
    def calculate_series_RC(self,magnitude, phase, frequency):
        """
        Calculate series resistance (R) and capacitance (C) from impedance magnitude, phase, and frequency.
        
        Args:
            magnitude (float): Impedance magnitude |Z| in ohms.
            phase (float): Phase angle in degrees.
            frequency (float): Frequency in Hz.
        
        Returns:
            tuple: (R, C) where R is resistance in ohms and C is capacitance in farads.
        """
        # Convert phase from degrees to radians
        phase_radians = math.radians(phase)

        # Calculate R (resistance)
        R = magnitude * math.cos(phase_radians)

        # Calculate X_C (capacitive reactance)
        X_C = magnitude * math.sin(phase_radians)

        # Avoid division by zero for frequency or X_C
        if frequency <= 0 or X_C == 0:
            raise ValueError("Frequency must be greater than 0 and X_C must not be zero.")

        # Calculate C (capacitance)
        C = 1 / (2 * math.pi * frequency * abs(X_C))

        return R, C

    def execute_impedance_sweep(self, measurement_method="P1R"):
        """
        Execute an impedance sweep measurement on the Bode100.
        Must call configure_sweep() and configure_receivers() first.
        
        Args:
            measurement_method (str, optional): Impedance measurement method. Default is "P1R".
                                              Options: "P1R", "TSER", "TPAR", "RSER", "RPAR"
        
        Returns:
            list: List of tuples containing (frequency, impedance_magnitude, impedance_phase, resistance, capacitance)
                 for each measurement point. Returns None if an error occurs.
        """
        try:
            # Configure measurement type and method
            self.configure_measurement(measurement_type="IMPEDANCE", measurement_method=measurement_method)
            
            # Execute the single sweep
            self._instrument.write(':INIT:IMM')       # Initiate measurement immediately
            self._instrument.query('*OPC?')           # Wait for completion
            
            # Read frequency data
            frequency_response = self._instrument.query(":SENS:FREQ:DATA?")
            frequency_list = [float(x) for x in frequency_response.split(',')]
            
            # Read impedance data (magnitude and phase combined)
            impedance_response = self._instrument.query(":CALC:DATA:SDAT?")
            impedance_list = [float(x) for x in impedance_response.split(',')]
            
            # Calculate point count from frequency data length
            point_count = len(frequency_list)
            
            # Split into magnitude and phase lists
            magnitude_list = impedance_list[0:point_count]
            phase_list = impedance_list[point_count:2*point_count]
            
            # Calculate R and C for each measurement point
            sweep_results = []
            for frequency, magnitude, phase in zip(frequency_list, magnitude_list, phase_list):
                try:
                    resistance, capacitance = self.calculate_series_RC(magnitude, phase, frequency)
                    sweep_results.append((frequency, magnitude, phase, resistance, capacitance))
                except ValueError as calc_error:
                    # Handle calculation errors gracefully
                    if self.debug:
                        print(f"Calculation error at {frequency} Hz: {calc_error}")
                    sweep_results.append((frequency, magnitude, phase, float('nan'), float('nan')))
            
            if self.debug:
                print(f"Impedance sweep completed: {len(sweep_results)} points")
                print(f"Frequency range: {min(frequency_list):.1f} Hz to {max(frequency_list):.1f} Hz")
                print(f"Impedance range: {min(magnitude_list):.2f} Ω to {max(magnitude_list):.2f} Ω")
                print(f"Phase range: {min(phase_list):.2f}° to {max(phase_list):.2f}°")
            
            return sweep_results
            
        except Exception as e:
            print(f"Error executing impedance sweep: {e}")
            return None

    def execute_gain_phase_sweep(self):
        """
        Execute a single gain and phase sweep measurement on the Bode100.
        Must call configure_sweep() and configure_receivers() first.
        
        Args:
            measurement_method (str, optional): Gain/phase measurement method. Default is "R1R2".
        
        Returns:
            list: List of tuples containing (frequency, gain_db, phase_deg) for each measurement point.
                 Returns None if an error occurs.
        """
        try:
            self.write_properties()  # Ensure properties are written to the instrument
            self.read_properties()
            self.trigger_single()
            self.wait_for_operation_to_complete()
            frequency_list, measurement_list = self.read_measurement_data()
            
            # Parse interleaved magnitude and phase data (per official documentation pattern)
            num_points = len(frequency_list)
            gain_list = measurement_list[0:num_points]          # First half: magnitude values in dB
            phase_list = measurement_list[num_points:num_points*2]  # Second half: phase values in degrees
            
            # Combine into final results list
            sweep_results = []
            for frequency, gain, phase in zip(frequency_list, gain_list, phase_list):
                sweep_results.append((frequency, gain, phase))
            
            if self.debug:
                print(f"Gain/phase sweep completed: {len(sweep_results)} points")
                print(f"Frequency range: {min(frequency_list):.1f} Hz to {max(frequency_list):.1f} Hz")
                print(f"Gain range: {min(gain_list):.2f} dB to {max(gain_list):.2f} dB")
                print(f"Phase range: {min(phase_list):.2f}° to {max(phase_list):.2f}°")
            
            return sweep_results
            
        except Exception as e:
            print(f"Error executing gain/phase sweep: {e}")
            return None

    def print_configuration(self):
        """
        Print the complete current configuration of the Bode100 instrument.
        Displays all current property values that will be written to the instrument.
        """
        print("=" * 60)
        print("BODE100 INSTRUMENT CONFIGURATION")
        print("=" * 60)
        
        # Basic instrument information
        print("\n📟 INSTRUMENT INFORMATION:")
        if self.is_connected:
            try:
                idn = self._instrument.query("*IDN?").strip()
                print(f"  Identity: {idn}")
            except:
                print("  Identity: Unable to query (instrument may be busy)")
        else:
            print("  Status: Not connected")
        
        # All Property Values
        print("\n⚙️  CURRENT PROPERTY VALUES:")
        print(f"  Attenuator Ch1: {self._attenuator[0]} dB")
        print(f"  Attenuator Ch2: {self._attenuator[1]} dB")
        print(f"  Bandwidth: {self._bandwidth} Hz")
        print(f"  Format: {self._format}")
        print(f"  Impedance Ch1: {int(self._impedance[0])} ohms")
        print(f"  Impedance Ch2: {int(self._impedance[1])} ohms")
        print(f"  Initiate Continuous: {'ON' if self._initiate_continuous else 'OFF'}")
        print(f"  Measurement Type: {self._measurement_type}")
        print(f"  Point Count: {self._point_count}")
        print(f"  Start Frequency: {self._start_frequency} Hz")
        print(f"  Source Level: {self._source_level} dBm")
        print(f"  Stop Frequency: {self._stop_frequency} Hz")
        print(f"  Sweep Type: {self._sweep_type}")
        print(f"  Trigger Source: {self._trigger_source}")
        print(f"  Z-Type: {self._z_type}")
        
        print(f"\n📊 FREQUENCY RANGE:")
        print(f"  {self._start_frequency:,.1f} Hz → {self._stop_frequency:,.0f} Hz")
        print(f"  Ratio: {self._stop_frequency/self._start_frequency:,.1f}:1")
        print(f"  Sweep: {self._sweep_type} with {self._point_count} points")
        
        print(f"\n🔧 MEASUREMENT SETUP:")
        print(f"  Type: {self._measurement_type}")
        if self._measurement_type == "Z":
            print(f"  Z-Parameter: {self._z_type}")
        print(f"  Format: {self._format}")
        print(f"  Bandwidth: {self._bandwidth} Hz")
        print(f"  Source Level: {self._source_level} dBm")
        print(f"  Trigger Source: {self._trigger_source}")
        print(f"  Continuous Initiation: {'ON' if self._initiate_continuous else 'OFF'}")
        
        print(f"\n📡 INPUT CONFIGURATION:")
        print(f"  Ch1: {int(self._impedance[0])} Ω, {self._attenuator[0]} dB attenuation")
        print(f"  Ch2: {int(self._impedance[1])} Ω, {self._attenuator[1]} dB attenuation")
        
        print("\n" + "=" * 60)
        print("Configuration display completed")
        print("=" * 60)

    def trigger_single(self):
        """
        Send a single trigger command to the Bode100 instrument.
        
        This command (:TRIGger[:SEQuence]:SINGle) generates a trigger regardless 
        of the trigger source selection. The command is implemented as an overlapped 
        command and is not completed until the measurement has ended. Therefore, 
        the end of the command CAN be awaited with an OPC command.
        
        Important Notes:
        - If the trigger is NOT in the "Waiting for Trigger" state, the command has 
          no effect and a "Trigger Ignored" error (nr. -211) is generated
        - Unlike :TRIGger[:SEQuence][:IMMediate], this command CAN be awaited
        - The command waits for measurement completion before returning
        
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        if not self.is_connected:
            print("✗ ERROR: Instrument not connected. Cannot send trigger.")
            return False
        
        try:
            # Send the single trigger command
            self._instrument.write(':TRIG:SING')
            
            if self.debug:
                print("✓ Single trigger command sent to Bode100")
            
            return True
            
        except Exception as e:
            print(f"✗ Error sending single trigger: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False

    def trigger_immediate(self):
        """
        Send an immediate trigger command to the Bode100 instrument.
        
        This command (:TRIGger[:SEQuence][:IMMediate]) generates a trigger regardless 
        of the trigger source selection. The command completes before the measurement 
        is finished and CANNOT be awaited with an OPC command.
        
        Important Notes:
        - If the trigger is NOT in the "Waiting for Trigger" state, the command has 
          no effect and a "Trigger Ignored" error (nr. -211) is generated
        - Unlike :TRIGger[:SEQuence]:SINGle, this command CANNOT be awaited
        - The command returns immediately, not waiting for measurement completion
        
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        if not self.is_connected:
            print("✗ ERROR: Instrument not connected. Cannot send immediate trigger.")
            return False
        
        try:
            # Send the immediate trigger command
            self._instrument.write(':TRIG:IMM')
            
            if self.debug:
                print("✓ Immediate trigger command sent to Bode100")
                print("  Note: Command completes immediately, not waiting for measurement")
            
            return True
            
        except Exception as e:
            print(f"✗ Error sending immediate trigger: {e}")
            if self.debug:
                print("  Note: If error -211 (Trigger Ignored), instrument may not be waiting for trigger")
                import traceback
                traceback.print_exc()
            return False

    def wait_for_operation_to_complete(self, timeout=30):
        """
        Wait for the current operation to complete using the *OPC? command.
        
        The *OPC? (Operation Complete Query) command will block until all pending 
        operations are completed, then return "1". This is useful for synchronizing
        with operations like trigger_single() that can be awaited.
        
        Args:
            timeout (float, optional): Maximum time to wait in seconds. Default is 30.
        
        Returns:
            bool: True if operation completed successfully, False if timeout or error
        """
        if not self.is_connected:
            print("✗ ERROR: Instrument not connected. Cannot wait for operation completion.")
            return False
        
        try:
            # Set a timeout for the query to prevent hanging indefinitely
            original_timeout = self._instrument.timeout
            self._instrument.timeout = timeout * 1000  # Convert to milliseconds
            
            if self.debug:
                print(f"⏳ Waiting for operation to complete (timeout: {timeout}s)...")
            
            # Send *OPC? query and wait for response
            response = self._instrument.query('*OPC?')
            
            # Restore original timeout
            self._instrument.timeout = original_timeout
            
            if response.strip() == "1":
                if self.debug:
                    print("✓ Operation completed successfully")
                return True
            else:
                print(f"✗ Unexpected response from *OPC?: {response}")
                return False
            
        except Exception as e:
            # Restore original timeout in case of error
            try:
                self._instrument.timeout = original_timeout
            except:
                pass
                
            print(f"✗ Error waiting for operation completion: {e}")
            if self.debug:
                print(f"  Note: This may indicate a timeout after {timeout} seconds")
                import traceback
                traceback.print_exc()
            return False

class BKPrecision891(Instrument):
    def __init__(self, model: str, address: str = None, debug: bool = False):
        """
        Initializes the BBKPrecision891 LCR Meter.

        :param model: Model of the instrument.
        :param address: VISA address of the instrument.
        :param debug: Enables debug mode if True.
        """
        super().__init__(model, address, debug)
        self._read_termination = '\n'
        self._write_termination = '\n'

    def initialize_cp(self, speed = "SLOW"):
        """
        Initialize the instrument for a parallel RC capacitance measurement

        Raises:
            RuntimeError: If the instrument is not connected.
            pyvisa.VisaIOError: If a communication error occurs during initialization.
        """
        # Check if the instrument is connected
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")

        try:
            #reset the meter
            self._instrument.write("*RST")

            # Set the measurement function to parallel capacitance
            self._instrument.write("MEAS:FUNC CPR")
            
            # Set the measurement speed 
            if speed.upper() not in ["FAST", "SLOW"]:
                speed = "SLOW"  # Default to "SLOW" if invalid
            self._instrument.write(f"MEAS:SPEED {speed}")
            
            # Configure the data format to return real numbers
            self._instrument.write("FORMAT:DATA REAL")
            
            # Set the AC level to 0.5
            self._instrument.write("LEVEL:AC 0.5")

        except pyvisa.VisaIOError as e:
            # Handle communication errors and log an appropriate message
            print(f"Failed to initialize: {e}")

    def measure_rc(self):
        """
        Measure capacitance and resistance using the instrument.

        The instrument returns a comma-separated string where the first value
        is capacitance (in farads) and the second is resistance (in ohms).

        Returns:
            tuple: (capacitance, resistance) as floats.

        Raises:
            RuntimeError: If the instrument is not connected.
            ValueError: If the response from the instrument is invalid.
            pyvisa.VisaIOError: If a communication error occurs during the operation.
        """
        # Check if the instrument is connected
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")

        try:
            # Send FETCH? command to retrieve capacitance and resistance
            response = self._instrument.query("FETCH?").strip()
            
            # Split the response into capacitance and resistance values
            values = response.split(",")

            # Ensure the response contains exactly two values
            if len(values) != 2:
                raise ValueError(f"Invalid response from instrument: {response}")

            # Convert the strings to floats
            capacitance = float(values[0])
            resistance = float(values[1])

            return capacitance, resistance
        except pyvisa.VisaIOError as e:
            # Handle communication errors and log an appropriate message
            print(f"Failed to fetch RC values: {e}")
            raise
        except ValueError as e:
            # Handle invalid response format
            print(f"Error processing instrument response: {e}")
            raise

    def set_frequency(self, frequency):
        """
        Set the frequency of the instrument for measurements.

        Args:
            frequency (float): The desired frequency in Hz.

        Raises:
            RuntimeError: If the instrument is not connected.
            ValueError: If the frequency is not a positive value.
            pyvisa.VisaIOError: If a communication error occurs during the operation.
        """
        # Check if the instrument is connected
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        # Validate the frequency
        if frequency <= 0:
            raise ValueError("Frequency must be a positive value.")

        try:
            # Set the frequency for measurements
            self._instrument.write(f"FREQ {frequency}")
        except pyvisa.VisaIOError as e:
            # Handle communication errors and log an appropriate message
            print(f"Failed to set frequency to {frequency} Hz: {e}")

class PowerSupply(Instrument):
    def __init__(self, model: str, address: str = None, debug: bool = False):
        """
        Initializes the PowerSupply.

        :param model: Model of the instrument.
        :param address: VISA address of the instrument.
        :param debug: Enables debug mode if True.
        """
        super().__init__(model, address, debug)

    def _channel_ok(self, channel: int) -> bool:
        """
        Validates if the channel number is between 1 and 4.

        :param channel: Channel number to validate.
        :return: True if valid, False otherwise.
        """
        if channel < 1 or channel > 4:
            print("Error: Channel must be between 1 and 4.")
            return False
        return True

    def get_current(self) -> float:
        """
        Retrieves the current setting from the power supply.

        :return: Current in amperes.
        """
        response = self._instrument.query("CURR?")
        return float(response)

    def get_voltage(self) -> float:
        """
        Retrieves the voltage setting from the power supply.

        :return: Voltage in volts.
        """
        response = self._instrument.query("VOLT?")
        return float(response)

    def get_max_current(self) -> float:
        """
        Retrieves the maximum current setting from the power supply.

        :return: Maximum current in amperes.
        """
        response = self._instrument.query("CURR? MAX")
        return float(response)

    def get_max_voltage(self) -> float:
        """
        Retrieves the maximum voltage setting from the power supply.

        :return: Maximum voltage in volts.
        """
        response = self._instrument.query("VOLT? MAX")
        return float(response)

    def get_supply_count(self, max_supply_count: int = 4) -> int:
        """
        Determines the number of available power supplies.

        :param max_supply_count: Maximum number of supplies to check.
        :return: Number of available supplies.
        """
        supply_count = 0
        self.set_beep_off()
        self.clear_errors()
        for i in range(1, max_supply_count + 1):
            self.set_channel(i)
            error = self.get_last_error()
            if error != 0:
                break
            supply_count += 1

        if supply_count == 0:
            voltage = self.get_voltage()
            error = self.get_last_error()
            if error == 0:
                self.set_voltage(voltage)
                error = self.get_last_error()
            if error == 0:
                supply_count = 1

        self.clear_errors()
        return supply_count

    def output_enabled(self) -> bool:
        """
        Checks if the output is enabled.

        :return: True if output is enabled, False otherwise.
        """
        response = self._instrument.query("OUTP?")
        return "0" not in response

    def measure_current(self) -> float:
        """
        Measures the current output.

        :return: Measured current in amperes.
        """
        response = self._instrument.query("MEAS:CURR:DC?")
        return float(response)

    def measure_voltage(self) -> float:
        """
        Measures the voltage output.

        :return: Measured voltage in volts.
        """
        response = self._instrument.query("MEAS:VOLT:DC?")
        return float(response)

    def set_channel(self, channel: int):
        """
        Sets the active channel on the power supply.

        :param channel: Channel number to set.
        """
        if self._channel_ok(channel):
            self._instrument.write(f"INST:NSEL {channel}")

    def set_output_off(self):
        """
        Turns off the output.
        """
        self._instrument.write("OUTP OFF")

    def set_output_on(self):
        """
        Turns on the output.
        """
        self._instrument.write("OUTP ON")

    def set_2_wire_sense(self):
        """
        Sets the sense to two wire
        """
        self._instrument.write(f"VOLT:SENS:SOUR INT")

    def set_4_wire_sense(self):
        """
        Sets the sense to four wire
        """
        self._instrument.write(f"VOLT:SENS:SOUR EXT")

    def set_voltage(self, voltage: float):
        """
        Sets the output voltage.

        :param voltage: Voltage to set in volts.
        """
        self._instrument.write(f"VOLT {voltage}")

    def set_voltage_and_current(self, channel: int, voltage: float, current: float):
        """
        Sets both voltage and current for a specific channel.

        :param channel: Channel number.
        :param voltage: Voltage to set in volts.
        :param current: Current to set in amperes.
        """
        if self._channel_ok(channel):
            if channel > 1:
                channel_string = f"CH{channel}"
                self._instrument.write(f"APPLY {channel_string},{voltage},{current}")
            else:
                self._instrument.write(f"APPLY {voltage},{current}")

    def set_current(self, current: float):
        """
        Sets the output current.

        :param current: Current to set in amperes.
        """
        self._instrument.write(f"CURR {current}")

class AFG3102(Instrument):
    def __init__(self, model: str = "AFG3102", address: str = None, debug: bool = False):
        """
        Initializes the AFG3102 Tektronix Arbitrary Function Generator.

        :param model: Model of the instrument (default is "AFG3102").
        :param address: VISA address of the instrument.
        :param debug: Enables debug mode if True.
        """
        super().__init__(model, address, debug)
        self._read_termination = '\n'
        self._write_termination = '\n'
        # Increase timeout for AFG3102 as it can be slower to respond
        self._timeout = 5000  # 5 seconds

    def _channel_ok(self, channel: int) -> bool:
        """
        Validates if the channel number is 1 or 2 (AFG3102 has 2 channels).

        :param channel: Channel number to validate.
        :return: True if valid, False otherwise.
        """
        if channel < 1 or channel > 2:
            if self.debug:
                print("Error: Channel must be 1 or 2 for AFG3102.")
            return False
        return True

    def set_waveform(self, channel: int, waveform: str):
        """
        Sets the waveform type for the specified channel.

        :param channel: Channel number (1 or 2).
        :param waveform: Waveform type ("SIN", "SQU", "TRI", "RAMP", "PULS", "NOIS", "DC", "USER").
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        valid_waveforms = ["SIN", "SQU", "TRI", "RAMP", "PULS", "NOIS", "DC", "USER"]
        if waveform.upper() not in valid_waveforms:
            raise ValueError(f"Invalid waveform. Must be one of: {valid_waveforms}")

        try:
            command = f"SOUR{channel}:FUNC:SHAP {waveform.upper()}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} waveform to {waveform.upper()}")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set waveform: {e}")

    def set_frequency(self, channel: int, frequency: float):
        """
        Sets the frequency for the specified channel.

        :param channel: Channel number (1 or 2).
        :param frequency: Frequency in Hz.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        if frequency <= 0:
            raise ValueError("Frequency must be positive.")

        try:
            command = f"SOUR{channel}:FREQ {frequency}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} frequency to {frequency} Hz")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set frequency: {e}")

    def set_amplitude(self, channel: int, amplitude: float, unit: str = "VPP"):
        """
        Sets the amplitude for the specified channel.

        :param channel: Channel number (1 or 2).
        :param amplitude: Amplitude value.
        :param unit: Unit ("VPP" for peak-to-peak, "VRMS" for RMS, "DBM" for dBm).
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        valid_units = ["VPP", "VRMS", "DBM"]
        if unit.upper() not in valid_units:
            raise ValueError(f"Invalid unit. Must be one of: {valid_units}")

        if amplitude < 0:
            raise ValueError("Amplitude must be non-negative.")

        try:
            # For Tektronix AFG3102, use appropriate command format
            if unit.upper() == "VPP":
                command = f"SOUR{channel}:VOLT {amplitude}"
            elif unit.upper() == "VRMS":
                command = f"SOUR{channel}:VOLT:RMS {amplitude}"
            else:  # DBM
                command = f"SOUR{channel}:VOLT:DBM {amplitude}"
            
            if self.debug:
                print(f"Setting amplitude with command: {command}")
            
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} amplitude to {amplitude} {unit.upper()}")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set amplitude: {e}")

    def set_offset(self, channel: int, offset: float):
        """
        Sets the DC offset for the specified channel.

        :param channel: Channel number (1 or 2).
        :param offset: DC offset in volts.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        try:
            command = f"SOUR{channel}:VOLT:OFFS {offset}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} offset to {offset} V")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set offset: {e}")

    def set_phase(self, channel: int, phase: float):
        """
        Sets the phase for the specified channel.

        :param channel: Channel number (1 or 2).
        :param phase: Phase in degrees.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        # Normalize phase to -180 to +180 degrees
        while phase > 180:
            phase -= 360
        while phase < -180:
            phase += 360

        try:
            command = f"SOUR{channel}:PHAS {phase}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} phase to {phase} degrees")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set phase: {e}")

    def set_output_on(self, channel: int):
        """
        Turns on the output for the specified channel.

        :param channel: Channel number (1 or 2).
        """
        self.set_output_state(channel, True)

    def set_output_off(self, channel: int): 
        """
        Turns off the output for the specified channel.

        :param channel: Channel number (1 or 2).
        """
        self.set_output_state(channel, False)

    def set_output_state(self, channel: int, state: bool):
        """
        Enables or disables the output for the specified channel.

        :param channel: Channel number (1 or 2).
        :param state: True to enable output, False to disable.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        try:
            state_str = "ON" if state else "OFF"
            command = f"OUTP{channel}:STAT {state_str}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} output {state_str}")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set output state: {e}")

    def set_output_impedance(self, channel: int, impedance: float):
        """
        Sets the output impedance for the specified channel.

        :param channel: Channel number (1 or 2).
        :param impedance: Output impedance in ohms (typical values: 50, 1000000 for high-Z).
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        if impedance <= 0:
            raise ValueError("Impedance must be positive.")

        try:
            command = f"OUTP{channel}:IMP {impedance}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} output impedance to {impedance} ohms")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set output impedance: {e}")

    def set_pulse_width(self, channel: int, width: float):
        """
        Sets the pulse width for pulse waveforms.

        :param channel: Channel number (1 or 2).
        :param width: Pulse width in seconds.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        if width <= 0:
            raise ValueError("Pulse width must be positive.")

        try:
            command = f"SOUR{channel}:PULS:WIDT {width}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} pulse width to {width} seconds")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set pulse width: {e}")

    def set_duty_cycle(self, channel: int, duty_cycle: float):
        """
        Sets the duty cycle for square wave or pulse waveforms.

        :param channel: Channel number (1 or 2).
        :param duty_cycle: Duty cycle as a percentage (0-100).
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        if duty_cycle < 0 or duty_cycle > 100:
            raise ValueError("Duty cycle must be between 0 and 100 percent.")

        try:
            command = f"SOUR{channel}:PULS:DCYC {duty_cycle}"
            self._instrument.write(command)
            if self.debug:
                print(f"Set channel {channel} duty cycle to {duty_cycle}%")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set duty cycle: {e}")

    def set_burst_mode(self, channel: int, mode: str, cycles: int = 1):
        """
        Configures burst mode for the specified channel.

        :param channel: Channel number (1 or 2).
        :param mode: Burst mode ("TRIG" for triggered, "GAT" for gated, "OFF" to disable).
        :param cycles: Number of cycles per burst (only for triggered mode).
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        valid_modes = ["TRIG", "GAT", "OFF"]
        if mode.upper() not in valid_modes:
            raise ValueError(f"Invalid burst mode. Must be one of: {valid_modes}")

        try:
            if mode.upper() == "OFF":
                command = f"SOUR{channel}:BURS:STAT OFF"
                self._instrument.write(command)
            else:
                # Enable burst mode
                self._instrument.write(f"SOUR{channel}:BURS:STAT ON")
                self._instrument.write(f"SOUR{channel}:BURS:MODE {mode.upper()}")
                if mode.upper() == "TRIG" and cycles > 0:
                    self._instrument.write(f"SOUR{channel}:BURS:NCYC {cycles}")
            
            if self.debug:
                print(f"Set channel {channel} burst mode to {mode.upper()}")
        except pyvisa.VisaIOError as e:
            print(f"Failed to set burst mode: {e}")

    def trigger_burst(self, channel: int):
        """
        Manually triggers a burst on the specified channel.

        :param channel: Channel number (1 or 2).
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return

        try:
            command = f"TRIG{channel}"
            self._instrument.write(command)
            if self.debug:
                print(f"Triggered burst on channel {channel}")
        except pyvisa.VisaIOError as e:
            print(f"Failed to trigger burst: {e}")

    def get_frequency(self, channel: int) -> float:
        """
        Gets the current frequency setting for the specified channel.

        :param channel: Channel number (1 or 2).
        :return: Frequency in Hz.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return float('nan')

        try:
            command = f"SOUR{channel}:FREQ?"
            response = self._instrument.query(command)
            return float(response.strip())
        except pyvisa.VisaIOError as e:
            print(f"Failed to get frequency: {e}")
            return float('nan')

    def get_amplitude(self, channel: int, unit: str = "VPP") -> float:
        """
        Gets the current amplitude setting for the specified channel.

        :param channel: Channel number (1 or 2).
        :param unit: Unit ("VPP", "VRMS", "DBM").
        :return: Amplitude value.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return float('nan')

        valid_units = ["VPP", "VRMS", "DBM"]
        if unit.upper() not in valid_units:
            raise ValueError(f"Invalid unit. Must be one of: {valid_units}")

        try:
            # For Tektronix AFG3102, try different command formats
            if unit.upper() == "VPP":
                command = f"SOUR{channel}:VOLT?"
            elif unit.upper() == "VRMS":
                command = f"SOUR{channel}:VOLT:RMS?"
            else:  # DBM
                command = f"SOUR{channel}:VOLT:DBM?"
            
            if self.debug:
                print(f"Querying amplitude with command: {command}")
            
            response = self._instrument.query(command)
            if self.debug:
                print(f"Response: {response}")
            return float(response.strip())
        except pyvisa.VisaIOError as e:
            print(f"Failed to get amplitude: {e}")
            # Try alternative command format
            try:
                alt_command = f"SOUR{channel}:VOLT:AMPL?"
                if self.debug:
                    print(f"Trying alternative command: {alt_command}")
                response = self._instrument.query(alt_command)
                return float(response.strip())
            except pyvisa.VisaIOError:
                return float('nan')

    def get_output_state(self, channel: int) -> bool:
        """
        Gets the current output state for the specified channel.

        :param channel: Channel number (1 or 2).
        :return: True if output is enabled, False otherwise.
        """
        if not self.is_connected:
            raise RuntimeError("Instrument is not connected.")
        
        if not self._channel_ok(channel):
            return False

        try:
            command = f"OUTP{channel}:STAT?"
            response = self._instrument.query(command).strip()
            return response == "1" or response.upper() == "ON"
        except pyvisa.VisaIOError as e:
            print(f"Failed to get output state: {e}")
            return False

    def enable_all_outputs(self):
        """
        Enables output for both channels.
        """
        self.set_output_state(1, True)
        self.set_output_state(2, True)

    def disable_all_outputs(self):
        """
        Disables output for both channels.
        """
        self.set_output_state(1, False)
        self.set_output_state(2, False)

    def configure_sine_wave(self, channel: int, frequency: float, amplitude: float, offset: float = 0.0):
        """
        Convenience method to configure a basic sine wave.

        :param channel: Channel number (1 or 2).
        :param frequency: Frequency in Hz.
        :param amplitude: Amplitude in Vpp.
        :param offset: DC offset in volts (default is 0.0).
        """
        self.set_waveform(channel, "SIN")
        self.set_frequency(channel, frequency)
        self.set_amplitude(channel, amplitude, "VPP")
        self.set_offset(channel, offset)

    def configure_square_wave(self, channel: int, frequency: float, amplitude: float, duty_cycle: float = 50.0, offset: float = 0.0):
        """
        Convenience method to configure a square wave.

        :param channel: Channel number (1 or 2).
        :param frequency: Frequency in Hz.
        :param amplitude: Amplitude in Vpp.
        :param duty_cycle: Duty cycle as a percentage (default is 50%).
        :param offset: DC offset in volts (default is 0.0).
        """
        self.set_waveform(channel, "SQU")
        self.set_frequency(channel, frequency)
        self.set_amplitude(channel, amplitude, "VPP")
        self.set_duty_cycle(channel, duty_cycle)
        self.set_offset(channel, offset)

# Example usage
if __name__ == "__main__":
    print(f"Starting Main")
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    print(f"Available resources: {resources}")

    if resources:
        instrument_address = resources[0]
        instrument = Instrument(model="Generic", address=instrument_address)
        instrument.debug = True  # Enable debug messages

        if instrument.check_connection():
            print(f"Connected to: {instrument.address}")
            print(f"Device ID: {instrument.id}")
            
            # Reset the instrument
            instrument.reset()
        else:
            print("Failed to connect to the instrument.")
        
        instrument.close()  # Ensure connection is closed
    else:
        print("No instruments found.")
