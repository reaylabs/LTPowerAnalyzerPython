# InstrumentDriver.py
# Description:
#  Driver class for interfacing with instruments using VISA.
#
# History:
#   11-29-2024  initial version

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
        if self._instrument:
            try:
                self._instrument.close()
                if self.debug:
                    print(f"Connection to {self._address} closed.")
            except pyvisa.VisaIOError as e:
                print(f"Failed to close the connection: {e}")
            finally:
                self._instrument = None
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

    def configure_sweep(self, start_frequency, stop_frequency, point_count=101, sweep_type="LINEAR"):
        """
        Configures the frequency sweep settings for the Bode 100.
        
        Args:
            start_frequency (float): Start frequency of the sweep in Hz.
            stop_frequency (float): Stop frequency of the sweep in Hz.
            point_count (int, optional): Number of points in the sweep. Default is 101.
            sweep_type (str, optional): Type of sweep, e.g., "LINEAR", "LOG". Default is "LINEAR".
        
        """
        valid_sweep_types = ["LINEAR", "LOG"]
        
        # Validate the sweep type
        if sweep_type not in valid_sweep_types:
            raise ValueError(f"Invalid sweep_type. Expected one of {valid_sweep_types}, got {sweep_type}")

        try:
            # Set the sweep type
            self._instrument.write(f'SWE:TYPE {sweep_type}')
            
            # Configure the sweep frequencies
            self._instrument.write(f'FREQ:START {start_frequency}')
            self._instrument.write(f'FREQ:STOP {stop_frequency}')
            
            # Configure the number of points in the sweep
            self._instrument.write(f'SWE:POIN {point_count}')
        except:
             print(f"Error setting sweep parameters : {e}")

    def execute_two_port_sweep(self, start_frequency, stop_frequency, bandwidth = "100Hz", point_count=2, sweep_type="LOG", magnitude_dbm = 2 ):
        """
        Make a two port impedance

        :param frequency: Frequency in Hz at which to measure.
        :param bandwidth: Bandwidth in Hz at which to measure.
        :param point_count: Number of points per measurement.
        :param sweep_type: LINEAR or LOG
        :return: A tuple containing (resistance, capacitance).
        """
        try:
            #set up the measurement
            self._instrument.write(':SENS:FREQ:STAR ' +str(start_frequency)) 
            self._instrument.write(':SENS:FREQ:STOP ' + str(stop_frequency))
            self._instrument.write(':SENS:SWE:POIN ' + str(point_count))
            self._instrument.write(':SENS:SWE:TYPE ' + sweep_type)
            self._instrument.write(':SENS:BAND ' + bandwidth)
            self._instrument.write(':CALC:PAR:DEF Z')  #Impedance measurement
            self._instrument.write(":SENS:Z:METH P1R")

            self._instrument.write(":CALC:FORM SLIN") # linear magnitude in Ohms + phase(deg)
            self._instrument.write(f":SOUR:POW {magnitude_dbm}")

            #setup the trigger
            self._instrument.write(':TRIG:SOUR BUS')  # Intializes trigger system to use BUS - to be used in combination with TRIG:SING and OPC
            self._instrument.write(':INIT:CONT ON') # Sets the trigger in continous mode. This way after a measurement the trigges gets back in state "ready" and waits for a further measurement.

            #run the sweep
            self._instrument.write(':TRIG:SING')
            self._instrument.query('*OPC?') # this command waits for all pending operations to finish and afterwards returns an 1

            #read the raw data
            gain_phase_results = self._instrument.query(":CALC:DATA:SDAT?")
            frequency_results = self._instrument.query(":SENS:FREQ:DATA?")

            #parse the raw data
            gain_phase_list = list(map(float, gain_phase_results.split(",")))
            magnitude_list = gain_phase_list[0:point_count]
            phase_list = gain_phase_list[point_count:]
            frequency_list = list(map(float, frequency_results.split(",")))

            #combine into a final sweep list
            sweep_list = []  # List to hold the final results

            # Iterate over frequency, magnitude, and phase lists together
            for frequency, magnitude, phase in zip(frequency_list, magnitude_list, phase_list):
                resistance, capacitance = self.calculate_series_RC(magnitude, phase, frequency)  # Calculate R and C
                # Append a tuple of all values to the final list
                sweep_list.append((frequency, magnitude, phase, resistance, capacitance))
            return sweep_list
        
        except Exception as e:
            print(f"Error execute two port sweep : {e}")
            return None

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
        instrument = Instrument(model = '3102')
        #instrument.debug = True  # Enable debug messages
        
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
