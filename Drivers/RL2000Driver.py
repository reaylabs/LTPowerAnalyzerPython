# RL2000Driver.py
# Description:
#   Driver for the RL2000 class

from SerialDeviceDriver import *
from datetime import datetime
import math
import sys

class RL2000Measurement:
    """Represents a measurement of current, voltage, and power for an RL2000 device."""
    
    def __init__(self):
        """Initializes the measurement object with default values of zero."""
        self.Current = [0, 0]  # List to store two current measurements
        self.Voltage = [0, 0]  # List to store two voltage measurements
        self.Power = [0, 0]    # List to store calculated power values

    def calculate_power(self):
        """Calculates power for each measurement index using the formula P = V * I."""
        self.Power = [self.Voltage[i] * self.Current[i] for i in range(2)]

class RL2000(SerialDevice): 

    #constructor
    def __init__(self, model_name, baudrate=9600, timeout=6):
        super().__init__(model_name, baudrate, timeout)
        # Basic set commands
        self._cmdSetCurrentLoad = "20"
        self._cmdServoCurrentMeter = "21"
        self._cmdSetCurrentMeterVoltage = "23"
        self._cmdSetCurrentMeterCompensation = "24"
        self._cmdSetCurrentLoadCompensation = "25"
        self._cmdSetSampleRate = "26"
        self._cmdSetAverageCount = "27"

        # Basic get commands
        self._cmdGetCurrentAndVoltage = "30"
        self._cmdGetCurrentMeterTemp = "31"
        self._cmdGetCurrentLoadTemp = "32"
        self._cmdGetSampleRate = "33"
        self._cmdGetAverageCount = "34"

        # Conversion constants
        self._cmdSetCurrentSampleRate = "42"
        self._cmdGetCurrentSampleRate = "43"
        self._cmdSetVoltageSampleRate = "44"
        self._cmdGetVoltageSampleRate = "45"

        # Voltmeter commands
        self._cmdReadVoltmeters = "50"

        # Current meter commands
        self._cmdReadCurrentMeter = "60"
        self._cmdSetCurrentMeterChannel = "61"
        self._cmdGetCurrentMeterChannel = "62"
        self._cmdSetCurrentMeterAutoscale = "64"
        self._cmdGetCurrentMeterAutoscale = "65"
        self._cmdSetCurrentMeterDac = "66"

        # Current load commands
        self._cmdReadCurrentLoad = "70"
        self._cmdReadCurrentMeterAndLoad = "71"
        self._cmdSetCurrentLoadDac = "72"
        self._cmdGetCurrentLoadChannel = "73"
        self._cmdGetCurrentLoadDacCode = "74"

        # Fan commands
        self._cmdSetFanSpeed = "80"
        self._cmdGetFanRpm = "81"

        # Sweep commands
        self._cmdSetSweepStartCurrent = "90"
        self._cmdSetSweepEndCurrent = "91"
        self._cmdSetSweepPointsPerDecade = "92"
        self._cmdSetSweepServoVoltage = "93"
        self._cmdExecuteSweep = "94"
        self._cmdExecuteMeasurement = "96"
        self._cmdExecuteSystemCheck = "97"

        # Calibration commands
        self._cmdStartVoltmeterCalibration = "100"
        self._cmdFinishVoltmeterCalibration = "101"
        self._cmdStartCurrentMeterVoltageCalibration = "102"
        self._cmdContinueCurrentMeterVoltageCalibration = "103"
        self._cmdFinishCurrentMeterVoltageCalibration = "104"
        self._cmdCurrentLoadDacCalibrationStart = "106"
        self._cmdCurrentLoadDacCalibrationContinue = "107"
        self._cmdCurrentLoadDacCalibrationFinish = "108"
        self._cmdCurrentMeterAndLoadZeroCalibration = "109"
        self._cmdCurrentMeterAndLoadFullScaleCalibration = "110"
        self._cmdPrintCalibration = "111"
        self._cmdCurrentMeterAndLoadLowScaleCalibration = "112"

        #Add error descriptions
        self.device_errors.add_error_description(5, "Communication Timeout")
        self.device_errors.add_error_description(6, "Current Meter Temperature")
        self.device_errors.add_error_description(7, "Current Load Temperature")
        self.device_errors.add_error_description(8, "Voltmeter 1 Timeout")
        self.device_errors.add_error_description(9, "Voltmeter 2 Timeout")
        self.device_errors.add_error_description(10, "Current Meter Timeout")
        self.device_errors.add_error_description(11, "Current Load Timeout")
        self.device_errors.add_error_description(12, "Servo Error")
        self.device_errors.add_error_description(13, "Fan Error")
        self.device_errors.add_error_description(14, "SOA Error")

    #delay to allow for settling
    async def delay_milliseconds(self, ms):
        """Delays for the given number of milliseconds."""
        await asyncio.sleep(ms / 1000)  # Convert milliseconds to seconds and delay

    #System Check

    def disable_automatic_system_check(self, port_index):
        """Disables automatic system check for the specified port by enabling test mode."""
        self.set_test_mode(port_index, 1)

    async def disable_all_automatic_system_check(self):
        """Asynchronously disables automatic system check for all available ports."""
        await self.set_all_test_mode(1)  # Enable test mode to disable automatic system checks
    
    def enable_automatic_system_check(self, port_index):
        """Enables automatic system check for the specified port by disabling test mode."""
        self.set_test_mode(port_index, 0)

    async def enable_all_automatic_system_check(self):
        """Asynchronously enables automatic system check for all available ports."""
        await self.set_all_test_mode(0)  # Disable test mode to enable automatic system checks

    def execute_system_check(self, port_index):
        """Executes a system check for the specified port.
           A system check will autorange all current meters,
           check for over voltages and temperature errors"""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdExecuteSystemCheck, port_index)  # Send the command to execute system check
                self.read_value(True, port_index)  # Read the response (ignoring the result)
            elif self.debug:
                print(f"Execute System Check: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Execute System Check Exception: {e}")  # Catch and print any exceptions that occur

    async def execute_all_system_check(self):
        """Asynchronously executes system checks for all available ports."""
        try:
            tasks = [asyncio.to_thread(self.execute_system_check, port_index)  
                    for port_index in range(len(self.serial_ports))]  # Create tasks for each port
            await asyncio.gather(*tasks)  # Execute all tasks concurrently
            if self.debug:
                print("All system checks executed successfully.")
        except Exception as e:
            print(f"Execute All System Check Exception: {e}")  # Catch and print any exceptions that occur

    # List generation
    def get_decade_value_list(self,start, end, points):
        """Generates a list of logarithmically spaced values with specified points per decade.
        
        Creates a logarithmic progression by placing the same number of points in each decade
        (factor of 10). The spacing scales proportionally with each decade.
        
        Args:
            start (float): Starting value of the sequence
            end (float): Ending value of the sequence  
            points (int): Number of points to place within each decade
        
        Returns:
            list: Logarithmically spaced values from start to end
            
        Example:
            get_decade_value_list(1, 100, 5) → 5 points per decade from 1 to 100
        """
        values = []
        
        # Prevent division by zero if no points specified
        if (points == 0):
            points = 1
            
        # Calculate interval for first decade: 9*start divided by points, normalized by 10
        interval = ((start*10) - start) / points / 10
        
        # Count how many complete decades span from start to end
        decade_count = int(math.log10(end/start))
    
        # Add one more decade if end value exceeds the last complete decade
        if (end > start*10**decade_count):
            decade_count += 1
            
        print(f"Decade count: {decade_count}")
        
        # Generate points for each decade
        for i in range(decade_count):
            # Starting value for current decade (start * 10^i)
            start_value = start * (10**i)
            
            # Scale interval by 10 for each successive decade
            interval = (interval * 10) 
            
            # Create specified number of points within this decade
            for j in range(points):
                value = start_value + (j * interval)
                
                # Only include values that don't exceed the end limit
                if (value <= end):
                    values.append(value)
                    
        # Always include the exact end value
        values.append(end)
        
        return values
    
    def get_linear_value_list(self, start_value, end_value, point_count):
        """Generates a list of linearly spaced values between start_value and end_value.
        
        Args:
            start_value (float): The starting value.
            end_value (float): The ending value.
            point_count (int): The total number of points.
        
        Returns:
            list: A list of linearly spaced values.
        """
        if point_count < 2:
            return [start_value, end_value]  # Ensure at least two values

        interval = (end_value - start_value) / (point_count - 1)
        values = [start_value + (i * interval) for i in range(point_count)]
        
        # Ensure the last value is exactly end_value
        values[-1] = end_value  

        return values
    
    # Open Devices
    def open_all_devices(self, print_status=True):
        """
        Open all connected RL2000 devices. Optionally print device info.
        Exits the program if no devices are found or an exception occurs.

        Args:
            print_status (bool): If True, prints device info and connection status.
        """
        try:
            if print_status:
                print("Searching For RL2000:\n")

            if self.check_connections():
                for i in range(self.port_count):
                    self.port_index = i
                    self.clear_errors()
                    if print_status:
                        self.print_device_info(i)
            else:
                if print_status:
                    print("No RL2000 Found.\nExiting program...")
                sys.exit(0)

        except Exception as e:
            print(f"Error opening RL2000 devices: {e}")
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

    #Read Current And Voltage
    def read_current_and_voltage(self, port_index):
        """Reads current and voltage values from the meter and returns an RL2000Measurement object."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                measurement = RL2000Measurement()  # Initialize the measurement object
                self.send_command(self._cmdGetCurrentAndVoltage, port_index)  # Send the read current and voltage command to the specified port
                
                # Read the first current and voltage values
                measurement.Current[0] = float(self.read_value(False, port_index))  
                measurement.Voltage[0] = float(self.read_value(False, port_index))  
                
                # Read the second current and voltage values
                measurement.Current[1] = float(self.read_value(False, port_index))  
                measurement.Voltage[1] = float(self.read_value(True, port_index))  

                measurement.calculate_power()  # Calculate power based on the current and voltage values
                return measurement  # Return the measurement object
            elif self.debug:
                print(f"Read Current and Voltage Port Not OK")  # Print a debug message if the port is not OK
                return None  # Return None if the port is not valid
        except Exception as e:
            print(f"Read Current and Voltage Exception: {e}")
            return None

    async def read_all_current_and_voltage(self):
        """Reads current and voltage values from all meters asynchronously."""
        try:
            # Create tasks for each current and voltage reading
            tasks = [asyncio.to_thread(self.read_current_and_voltage, port_index) 
                    for port_index in range(len(self.serial_ports))]

            # Execute all tasks concurrently and gather results
            current_voltage_values = await asyncio.gather(*tasks)  
            return current_voltage_values  # Return a list of current and voltage readings from all meters
        except Exception as e:
            print(f"Error reading current and voltage: {e}")  # Print the exception message if an error occurs
            return None  # Return None in case of error

    #Read Currents
    def read_currents(self, port_index):
        """Sends a command to read current values and retrieves the readings."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdReadCurrentMeterAndLoad, port_index)  # Send the read current command to the specified port
                current1 = float(self.read_value(False, port_index))  # Read the first current value
                current2 = float(self.read_value(True, port_index))   # Read the second current value
                return current1, current2  # Return both current readings as a tuple
            elif self.debug:
                print(f"Read Currents Port Not OK")  # Print a debug message if the port is not OK
                return None  # Return None if the port is not valid
        except Exception as e:
            print(f"Read Currents Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs 
        
    async def read_all_currents(self):
        """Asynchronously reads current values from all available serial ports."""
        try:
            # Create tasks for each current reading
            tasks = [asyncio.to_thread(self.read_currents, port_index)  
                    for port_index in range(len(self.serial_ports))]  
            
            # Execute all tasks concurrently and gather results
            current_values = await asyncio.gather(*tasks)  
            return current_values  # Return a list of current readings from all ports
        except Exception as e:
            print(f"Error reading all currents: {e}")  # Print the exception message if an error occurs
            return None  # Return None in case of error

    #Read Fan Speed
    def read_fan_speed(self, port_index):
        """Sends a command to read the fan speed."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdGetFanRpm, port_index)  # Send the read current command to the specified port
                rpm = float(self.read_value(True, port_index))  # Read the first current value
                return rpm
            elif self.debug:
                print(f"Read Fan Speed Port Not OK")  # Print a debug message if the port is not OK
                return None  # Return None if the port is not valid
        except Exception as e:
            print(f"Read Fan Speed Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs 

    #Read Temperatures
    def read_temperatures(self, port_index):
        """Sends commands to read load and meter temperatures and retrieves both temperature readings."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the command to read the load temperature
                self.send_command(self._cmdGetCurrentLoadTemp, port_index)  
                load_temp = float(self.read_value(True, port_index))  # Read the load temperature
                
                # Send the command to read the meter temperature
                self.send_command(self._cmdGetCurrentMeterTemp, port_index)  
                meter_temp = float(self.read_value(True, port_index))  # Read the meter temperature
                
                return meter_temp, load_temp  # Return both temperature readings as a tuple
            elif self.debug:
                print(f"Read Temperatures Port Not OK")  # Print a debug message if the port is not OK
                return None
        except Exception as e:
            print(f"Read Temperatures Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    async def read_all_temperatures(self):
        """Asynchronously reads load and meter temperatures from all available serial ports."""
        try:
            tasks = [asyncio.to_thread(self.read_temperatures, port_index)  
                    for port_index in range(len(self.serial_ports))]  # Create tasks for each temperature reading
            
            # Execute all tasks concurrently and gather results
            temperature_values = await asyncio.gather(*tasks)
            return temperature_values  # Return a list of temperature readings from all ports
        except Exception as e:
            print(f"Read All Temperatures Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    #Read Voltages
    def read_voltages(self, port_index):
        """Sends a command to read voltmeter values and retrieves two voltage readings."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdReadVoltmeters, port_index)  # Send the read voltmeter command to the specified port
                voltage1 = float(self.read_value(False, port_index))  # Read the first voltage value
                voltage2 = float(self.read_value(True, port_index))   # Read the second voltage value
                return voltage1, voltage2  # Return both voltage readings as a tuple
            elif self.debug:
                print(f"Read Voltages Port Not OK")  # Print a debug message if the port is not OK
                return None
        except Exception as e:
            print(f"Read Voltmeters Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    async def read_all_voltages(self):
        """Asynchronously reads voltmeter values from all available serial ports."""
        try:
            tasks = [asyncio.to_thread(self.read_voltages, port_index)  
                    for port_index in range(len(self.serial_ports))]  # Create tasks for each voltmeter
            voltmeter_values = await asyncio.gather(*tasks)  # Execute all tasks concurrently and gather results
            return voltmeter_values  # Return a list of voltmeter readings from all ports
        except Exception as e:
            print(f"Read All Voltages Exception: {e}")  # Catch and print any exceptions that occur
            return None  # Return None if an error occurs

    # Set Load Current
    def set_current_load(self, port_index, value):
        """Sets the current load for the specified port."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetCurrentLoad, port_index)  # Send the command to set the current load
                self.send_value(value, port_index)  # Send the specified value for the current load
                self.read_value(True, port_index)  # Read the response (ignoring the result)
            elif self.debug:
                print(f"Set Current Load: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
                print(f"Set Current Load Exception: {e}")  # Catch and print any exceptions that occur
        
    async def set_all_current_loads(self, value_array):
        """Asynchronously sets the current load for all available ports."""
        try:
            tasks = [
                asyncio.to_thread(self.set_current_load, port_index, value_array[port_index])
                for port_index in range(len(self.serial_ports))
            ]
            await asyncio.gather(*tasks)  # Execute all tasks concurrently
        except Exception as e:
            print(f"Set All Current Loads Exception: {e}")

    async def set_shared_load_current(self, total_load_current):
        """Asynchronously shares the given current evenly among all meters."""
        shared_load_current = total_load_current / self.port_count
        try:
            tasks = [asyncio.to_thread(self.set_current_load(port_index, shared_load_current))  
                    for port_index in range(len(self.serial_ports))]  # Create tasks for each current load
        except Exception as e:
            print(f"Set Shared Load Current Exception: {e}")  # Catch and print any exceptions that occur

    def set_fan_speed(self, port_index, value):
        """Sets the fan speed (0-100)."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdSetFanSpeed, port_index)  # Send the command to set the fan speed
                self.send_value(value, port_index)  # Send the specified value for the current load
                self.read_value(True, port_index)  # Read the response (ignoring the result)
            elif self.debug:
                print(f"Set Fan Speed: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
                print(f"Set Fan Speed Exception: {e}")  # Catch and print any exceptions that occur

    # Set Sample Rate
    def set_sample_rate(self, port_index, sample_rate):
        """Sets the sample rate (0 = slowest, 3 = fastest)for the specified port."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                sample_rate = max(0, min(sample_rate, 3))  # Clamp sample rate between 0 and 3
                self.send_command(self._cmdSetSampleRate, port_index)  # Send the command
                self.send_value(sample_rate, port_index)  # Send the sample rate value
                self.read_value(True, port_index)  # Read the response
            elif self.debug:
                print(f"Set Sample Rate: Device not ready on port {port_index}")
        except Exception as e:
            print(f"Set Sample Rate Exception: {e}")  

    async def set_all_sample_rates(self, sample_rate):
        """Asynchronously sets the sample rate for all available ports."""
        try:
            tasks = [asyncio.to_thread(self.set_sample_rate, port_index, sample_rate)  
                     for port_index in range(len(self.serial_ports))]
            await asyncio.gather(*tasks)  # Execute all tasks concurrently
        except Exception as e:
            print(f"Set All Sample Rates Exception: {e}")  

    # Set servo voltage
    def set_servo_voltage(self, port_index, voltage, channel):
        """Sets the servo voltage for the specified port and channel."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                # Send the command to set the servo voltage
                self.send_command(self._cmdServoCurrentMeter, port_index)
                # Send the voltage value for the servo
                self.send_value(voltage, port_index)
                # Send the channel value (0 = voltage1, 1 = voltage2)
                self.send_value(channel, port_index)
                # Read the response (ignoring the result)
                self.read_value(True, port_index)
            elif self.debug:
                print(f"Set Servo Voltage: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Set Servo Voltage Exception: {e}")  # Catch and print any exceptions that occur

    async def set_all_servo_voltages(self, voltage_array, channel_array):
        """Asynchronously sets the servo voltage for all available ports."""
        try:
            tasks = [
                asyncio.to_thread(self.set_servo_voltage, port_index, voltage_array[port_index], channel_array[port_index])
                for port_index in range(len(self.serial_ports))
            ]
            await asyncio.gather(*tasks)  # Execute all tasks concurrently
        except Exception as e:
            print(f"Set All Servo Voltages Exception: {e}")

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

    async def set_all_test_mode(self, value):
        """Asynchronously sets the test mode for all available serial ports."""
        try:
            tasks = [
                asyncio.to_thread(self.set_test_mode, port_index, value)
                for port_index in range(len(self.serial_ports))  # Create tasks for each port
            ]
            await asyncio.gather(*tasks)  # Execute all tasks concurrently
            if self.debug:
                print("All test modes set successfully.")
        except Exception as e:
            print(f"Set All Test Mode Exception: {e}")  # Catch and print any exceptions that occur

    #voltmeter Calibration
    def StartVoltmeterCalibration(self, port_index, voltage):
        """Starts voltmeter calibration for the specified port with the given voltage."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdStartVoltmeterCalibration, port_index)  # Send the command to start voltmeter calibration
                self.send_value(voltage, port_index)  # Send the specified voltage value
                self.read_value(True, port_index)  # Read the response (ignoring the result)
            elif self.debug:
                print(f"Start Voltmeter Calibration: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Start Voltmeter Calibration Exception: {e}")  # Catch and print any exceptions that occur

    def FinishVoltmeterCalibration(self, port_index):
        """Finishes voltmeter calibration for the specified port."""
        try:
            if self.port_ok(port_index):  # Check if the specified port is valid
                self.send_command(self._cmdFinishVoltmeterCalibration, port_index)  # Send the command to finish voltmeter calibration
                self.read_value(True, port_index)  # Read the response (ignoring the result)
            elif self.debug:
                print(f"Finish Voltmeter Calibration: Device not ready on port {port_index}")  # Debug message if the device is not ready
        except Exception as e:
            print(f"Finish Voltmeter Calibration Exception: {e}")  # Catch and print any exceptions that occur


