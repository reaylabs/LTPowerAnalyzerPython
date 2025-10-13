# SerialDeviceDriver.py
# Description:
#   Base driver for the Arduino based SerialDevice

import asyncio
import serial
import serial.tools.list_ports

class SerialDeviceInfo:
    """
    Represents detailed information about a serial device.
    """
    def __init__(self):
        """
        Initializes a new instance of the SerialDeviceInfo class with default values.
        """
        self.ModelName: str = ""
        self.FirmwareVersion: str = ""
        self.BoardVersion: str = ""
        self.SerialNumber: str = ""
        self.UsbPower: float = 0.0  # Power drawn over USB in watts
        self.ManufactureDate: str = ""  # Manufacture Date in day-month-year
        self.CalibrationDate: str = ""  # Calibration Date in day-month-year
        self.Connected: bool = False
        self.PortName: str = ""
        self.Error: int = 0  # Error code, 0 indicates no error      

class SerialDeviceErrors:
    """
    Base class for SerialDevice firmware error codes
    """

    def __init__(self):
        # Backing field for errorFlags (uint equivalent)
        self.error_flags = 0

        # Dictionary to hold error descriptions
        self.error_descriptions = {
            0: "No Error",
            1: "Command Not Found",
            2: "Measurement Timeout",
            3: "Invalid Value",
            4: "Parse Error",
            5: "Communication Timeout"
        }

    @property
    def error(self):
        """Getter for errorFlags"""
        return self.error_flags

    @error.setter
    def error(self, value):
        """Setter for errorFlags"""
        self.error_flags = value

    def set_error(self, bit):
        """Sets an error bit based on the bit number"""
        if 0 <= bit < 32:
            self.error_flags |= (1 << bit)

    def clear_error(self, bit):
        """Clears an error bit based on the bit number"""
        if 0 <= bit < 32:
            self.error_flags &= ~(1 << bit)

    def clear_all_errors(self):
        """Clears all errors"""
        self.error_flags = 0

    def get_error_description(self, bit):
        """Gets the error description for a specific bit number"""
        return self.error_descriptions.get(bit, "Unknown Error")

    def get_error_summary(self):
        """Gets a description of all the errors that have been set"""
        errors = []
        for i in range(32):
            if (self.error_flags & (1 << i)) != 0:
                errors.append(self.get_error_description(i))
        return " | ".join(errors)

    def add_error_description(self, bit, description):
        """Method to allow derived classes to add new error descriptions"""
        if 0 <= bit < 32 and bit not in self.error_descriptions:
            self.error_descriptions[bit] = description

class SerialDevice:
    def __init__(self, model_name, baudrate=9600, timeout=6): 
        #Commands
        self._cmd_model_name = "1"  # Command to identify the model
        self._cmd_get_device_info = "2"  # Command to get device information
        self._cmd_blink_led_red = "3"  # Command to blink the red LED
        self._cmd_set_led_red = "4"  # Command to set the red LED
        self._cmd_set_led_green = "5"  # Command to set the green LED
        self._cmd_set_led_off = "6"  # Command to turn off the LEDs
        self._cmd_get_error = "7"  # Command to get the last error
        self._cmd_clear_errors = "8"  # Command to clear errors
        self._cmd_set_manufacture_date = "249"  # Command to set manufacture date
        self._cmd_get_manufacture_date = "250"  # Command to get manufacture date
        self._cmd_set_calibration_date = "251"  # Command to set calibration date
        self._cmd_get_calibration_date = "252"  # Command to get calibration date
        self._cmd_set_test_mode = "253"  # Command to set test mode
        self._cmd_set_board_revision = "254"  # Command to set board revision
        self._cmd_toggle_debug_mode = "255"  # Command to toggle debug mode

        #global variables
        self._model_name = model_name
        self._connected = False
        self._debug = False
        self._device_info = SerialDeviceInfo()
        self.device_errors = SerialDeviceErrors()

        self._baudrate = baudrate
        self._timeout = timeout
        self._error = None  # To store the error code (if any)
        self._error_device_index = 0 # The device that generated the error
        self._port_index = 0  # Default to first device
        self.serial_ports = []  # Store matching serial ports for this device instance
        self._checked_ports = set()  # Track ports that have already been checked
    
    def __del__(self):
        """
        Ensures the connection is closed when the object is deleted.
        """
        self.close()

    @property
    def debug(self):
        """Getter for debug property."""
        return self._debug

    @debug.setter
    def debug(self, value):
        """Setter for debug property."""
        if isinstance(value, bool):  # Ensure the value is a boolean
            self._debug = value
        else:
            raise ValueError("Debug must be a boolean value.")
        
    @property
    def error(self):
        """Returns the error."""
        return self._error
    
    @property
    def error_description(self):
        """Returns the error description."""
        self.device_errors.clear_all_errors()
        hexString = "0x" + str(self.error)
        self.device_errors.error = int(hexString, 16)
        return self.device_errors.get_error_summary()
    
    @property
    def error_device_index(self):
        """Returns the index of the device that generated the error."""
        return self._error_device_index  
    
    @property
    def is_open(self):
        """Returns True if the serial port is open, False otherwise."""
        return self.port_ok()
    
    @property
    def port(self):
        """
        Property to get the current serial port based on the selected port index.

        :return: The current serial port object.
        """
        try:
            if self.port_ok():  # Ensure the port is open and ready
                return self.serial_ports[self.port_index]
            else:
                raise Exception("Serial port is not open.")
        except Exception as e:
            if self.debug:
                print(f"Error: {e}")
            return None

    @property
    def port_count(self):
        """Returns the count of connected serial ports."""
        return len([ser for ser in self.serial_ports if ser.is_open])
    
    @property
    def port_index(self):
        """Get the current port index."""
        return self._port_index
    
    @port_index.setter
    def port_index(self, index):
        """Set the index for the serial port."""
        if 0 <= index < len(self.serial_ports):
            self._port_index = index
            self.ser = self.serial_ports[index]  # Set the serial connection to the selected port
        else:
            print(f"Invalid port_index: {index}. No port selected.")

    def check_connections(self):
        """
        Search through all available COM ports and add matching devices to the serial_ports list.

        This method checks all the COM ports and attempts to connect to devices by sending 
        a command to get the model name. Devices that match the expected model name are added 
        to the serial_ports list for further communication.

        :return: True if at least one matching device is found and successfully connected, 
                False otherwise.
        """
        ports = serial.tools.list_ports.comports()

        # Remove any ports from _checked_ports that are no longer available
        current_ports = {port_info.device for port_info in ports}
        self._checked_ports.intersection_update(current_ports)  # Retain only the available ports

        for port_info in ports:
            if port_info.device in self._checked_ports:
                # Skip ports that have already been checked
                continue

            if self._debug:
                print(f"Checking port: {port_info.device}")
            try:
                # Open the port and check the device model
                temp_ser = serial.Serial(port_info.device, baudrate=self._baudrate, timeout=0.5)
                if self._debug:
                    print(f"Opening port: {port_info.device}")
                
                # Send the command to get the model name
                self.writeln(temp_ser, self._cmd_model_name)

                # Read the response
                response = self.readln(temp_ser, read_error=True)
                
                # If the response matches the model name, add it to the serial_ports list
                if response == self._model_name:
                    if self._debug:
                        print(f"Device found on {port_info.device}")
                    
                    # Add port to the list if not already added
                    if not any(port.portstr == port_info.device for port in self.serial_ports):
                        self.serial_ports.append(temp_ser)  # Add the serial connection to the list
                        self.port.timeout = self._timeout

                self._checked_ports.add(port_info.device)  # Mark this port as checked
                
            except (serial.SerialException, UnicodeDecodeError, OSError) as e:
                if self._debug:
                    print(f"Error checking port {port_info.device}: {e}")

        # If no matching devices were found, set connected to False
        if len(self.serial_ports) == 0:
            self._connected = False
            if self._debug:
                print("No matching device found.")
            return False

        self._connected = True
        self.port_index = 0  # Set the default port index to the first device found
        for i in range(len(self.serial_ports)):
            self.serial_ports[i].timeout = self._timeout
        if self._debug:
            print(f"Device connected: {self.port.portstr}")
        return True

    def port_ok(self, port_index = None):
        """
        Check if the serial port is open and connected.
        :return: True if the port is open and connected, False otherwise.
        """
        if (port_index is None):
            index = self.port_index
        else:
            index = port_index  
        if (len(self.serial_ports) == 0):
            return False  
        if self.serial_ports[index] and self.serial_ports[index].is_open:
            return True
        return False
    
    def clear_errors(self):
        """
        Send the command to clear all errors and receive the error code.
        :return: Error code if any, otherwise None.
        """ 
        return_error = 0 
        for port_index in range(len(self.serial_ports)):
            self.send_command(self._cmd_clear_errors, port_index)
            error = self.read_value(True, port_index)
            if (error != 0):
                return_error = error
        return return_error

       # return self.execute_set_command(self._cmd_clear_errors, "Clear Errors")
    
    def close(self):
        """
        Close the serial connection if open.

        This method iterates through all serial ports and closes any that are open.
        If no open connections are found, it prints a message.
        Any exceptions encountered during the process are caught and logged.
        """
        if len(self.serial_ports) == 0:
            print("No open connection to close.")
            return

        for port in self.serial_ports:
            try:
                if port and port.is_open:
                    port.close()
                    if self._debug:
                        print(f"Closed connection on port: {port.portstr}")
            except Exception as e:
                print(f"Error closing port {port.portstr}: {e}")

    def execute_get_command(self, command, description):
        """
        Execute a get command, evaluate self._error, and return the device's response.

        :param command: Command to send.
        :param description: Description of the command for debugging/logging purposes.
        :return: Response from the device if successful, otherwise None.
        """
        if self.port_ok():
            try:
                # Send the command
                self.writeln(self.port, command)
                
                # Read the response from the device
                response = self.readln(self.port, read_error=True)
                
                # Check for errors
                if self._error:
                    if self._debug:
                        print(f"Error while executing '{description}': {self._error}")
                    return None
                else:
                    if self._debug:
                        print(f"'{description}' executed successfully: {response}")
                    return response
            except Exception as e:
                print(f"Exception during '{description}': {e}")
                return None
        else:
            print(f"Cannot execute '{description}': Serial port is not open.")
            return None

    def execute_set_command(self, command, description, value=None):
        """
        Execute a set command and handle the response.

        :param command: Command to send.
        :param description: Description of the command for debugging/logging purposes.
        :param value: Optional value to send after the command.
        :return: Error code if any, otherwise None.
        """
        if self.port_ok():
            try:
                # Send the initial command
                self.writeln(self.port, command)
                
                # If a value is provided, convert it to a string and send it
                if value is not None:
                    value_str = str(value)
                    self.writeln(self.port, value_str)
                    if self._debug:
                        print(f"Sent value '{value_str}' for '{description}'")

                # Read the response and check for errors
                response = self.readln(self.port, read_error=True)
                if self._error:
                    if self._debug:
                        print(f"Error while executing '{description}': {self._error}")
                else:
                    if self._debug:
                        print(f"'{description}' executed successfully: {response}")
                return self._error
            except Exception as e:
                print(f"Exception during '{description}': {e}")
                return None
        else:
            print(f"Cannot execute '{description}': Serial port is not open.")
            return None

    def get_device_info(self, port_index=None):
        """
        Get device info for a given port index or the current one if not specified.

        Args:
            port_index (int, optional): Specific port index. Defaults to self.port_index.

        Returns:
            SerialDeviceInfo or None
        """
        if port_index is not None:
            if not self.port_ok(port_index):
                if self.debug:
                    print(f"Port {port_index} not OK.")
                return None
            self.port_index = port_index

        if not self.port_ok():
            if self.debug:
                print(f"Port {self.port_index} not OK.")
            return None

        try:
            info = SerialDeviceInfo()
            info.PortName = self.port.portstr
            info.Connected = True

            self.writeln(self.port, self._cmd_get_device_info)
            info.ModelName = self.readln(self.port, read_error=False)
            if not self.error:
                info.FirmwareVersion = self.readln(self.port, read_error=False)
            if not self.error:
                info.BoardVersion = self.readln(self.port, read_error=False)
            if not self.error:
                info.SerialNumber = self.readln(self.port, read_error=False)
            if not self.error:
                info.UsbPower = self.readln(self.port, read_error=False)
            if not self.error:
                info.ManufactureDate = self.readln(self.port, read_error=False)
            if not self.error:
                info.CalibrationDate = self.readln(self.port, read_error=True)

            info.Error = self._error
            return info

        except Exception as e:
            print(f"Error during get_device_info: {e}")
            return None
 
    def get_error(self, port_index=None):
        """
        Get the last error code from the specified port or the currently selected port.

        Args:
            port_index (int, optional): Port index to use. Defaults to current port.

        Returns:
            str or None: Error code as a string, or None if an error occurs.
        """
        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_get_command(self._cmd_get_error, "Get Last Error")

        except Exception as e:
            print(f"Get Error Exception: {e}")
            return None

    def blink_led_red(self, port_index = None):
        """
        Blink the red LED on the specified port or the currently selected port.

        Args:
            port_index (int, optional): Port index to use. If None, uses current port_index.

        Returns:
            int or None: Error code, or None on failure.
        """
        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_blink_led_red, "Blink LED Red")

        except Exception as e:
            print(f"Blink LED Red Exception: {e}")
            return None

    def read_value(self, read_error, port_index):
        try:
            return self.readln(self.serial_ports[port_index],read_error)
        except Exception as e:
            print(f"Read Value Exception': {e}")
            return None
          
    def send_command(self, command, port_index):
        try:
            self.writeln(self.serial_ports[port_index],command)
            return True
        except Exception as e:
            print(f"Send Command Exception': {e}")
            return False
    
    def send_value(self, value, port_index):
        # Convert the value to a string
        value_str = str(value)
        # Call send_command with the converted value
        return self.send_command(value_str, port_index)     

    def set_board_revision(self, board_revision, port_index=None):
        """
        Set the board revision by encoding integer and fractional parts into a 16-bit value,
        and sending it to the specified port or the currently selected one.

        Args:
            board_revision (float or int): Board revision, e.g. 1.05.
            port_index (int, optional): Target port index. If None, uses current port_index.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        if not isinstance(board_revision, (float, int)):
            print("Invalid board revision format. Provide a numeric value.")
            return None

        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            # Extract integer and fractional parts
            integer_part = int(board_revision)
            fractional_part = int((board_revision - integer_part) * 100)

            # Combine into 16-bit value
            revision = (integer_part << 8) | (fractional_part & 0xFF)

            # Send the command
            return self.execute_set_command(self._cmd_set_board_revision, "Set Board Revision", value=str(revision))

        except Exception as e:
            print(f"Error during board revision set operation: {e}")
            return None

    def set_calibration_date(self, date, port_index=None):
        """
        Send the command to set the calibration date in the format mm-dd-yyyy 
        to the specified port or currently selected one.

        Args:
            date (str): Calibration date in the format mm-dd-yyyy.
            port_index (int, optional): Port index to use. Defaults to current port.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        if not isinstance(date, str) or not self.validate_date_format(date):
            print("Invalid date format. Use mm-dd-yyyy.")
            return None

        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_set_calibration_date, "Set Calibration Date", value=date)

        except Exception as e:
            print(f"Error during calibration date set operation: {e}")
            return None

    def set_led_green(self, port_index=None):
        """
        Turn on the green LED on the specified port or currently selected port.

        Args:
            port_index (int, optional): Port index to use. If None, uses current port.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_set_led_green, "Set LED Green")

        except Exception as e:
            print(f"Set LED Green Exception: {e}")
            return None

    def set_led_off(self, port_index=None):
        """
        Turn off the LED on the specified port or currently selected port.

        Args:
            port_index (int, optional): Port index to use. If None, uses current port.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_set_led_off, "Set LED Off")

        except Exception as e:
            print(f"Set LED Off Exception: {e}")
            return None

    def set_led_red(self, port_index=None):
        """
        Turn on the red LED on the specified port or currently selected port.

        Args:
            port_index (int, optional): Port index to use. If None, uses current port.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_set_led_red, "Set LED Red")

        except Exception as e:
            print(f"Set LED Red Exception: {e}")
            return None

    def set_manufacture_date(self, date, port_index=None):
        """
        Send the command to set the manufacture date in the format mm-dd-yyyy 
        to the specified port or currently selected one.

        Args:
            date (str): Manufacture date in the format mm-dd-yyyy.
            port_index (int, optional): Port index to use. Defaults to current port.

        Returns:
            int or None: Error code if any, otherwise None.
        """
        if not isinstance(date, str) or not self.validate_date_format(date):
            print("Invalid date format. Use mm-dd-yyyy.")
            return None

        try:
            if port_index is not None:
                if not self.port_ok(port_index):
                    if self.debug:
                        print(f"Port {port_index} not OK.")
                    return None
                self.port_index = port_index

            if not self.port_ok():
                if self.debug:
                    print(f"Port {self.port_index} not OK.")
                return None

            return self.execute_set_command(self._cmd_set_manufacture_date, "Set Manufacture Date", value=date)

        except Exception as e:
            print(f"Error during manufacture date set operation: {e}")
            return None

    def readln(self, ser, read_error=False):
        """
        Read a line of text from the serial port and optionally handle the error code.

        :param ser: The serial port object used for communication.
        :param read_error: Flag indicating whether to read and process an error code after the response. Defaults to False.
        :return: The response from the serial port as a string.
        """
        response = ser.readline().decode('utf-8').strip()
        if self._debug:
            print(f"Readln Response: {response}")
        
        if read_error:
            # If read_error is True, read a second response and store it as an integer error code
            error_response = ser.readline().decode('utf-8').strip()
            if self._debug:
                print(f"Readln Error Response: {error_response}")
            try:
                self._error = int(error_response)
                self._error_device_index = self._port_index
                if self._debug:
                    print(f"Readln Error code: {self._error}")
            except ValueError:
                if self._debug:
                    print(f"Invalid error code received: {error_response}")
                self._error = None

        return response

    def validate_date_format(self, date):
        """
        Validate that the provided date is in the format mm-dd-yyyy.

        :param date: The date string to validate.
        :return: True if the date matches the mm-dd-yyyy format, False otherwise.
        """
        import re
        return bool(re.match(r"^\d{2}-\d{2}-\d{4}$", date))

    def writeln(self, ser, command):
        """
        Append a newline character to the command and send it to the serial port.

        :param ser: The serial port object used for communication.
        :param command: The command string to send.
        """
        ser.write(f"{command}\n".encode('utf-8'))
        ser.flush()

