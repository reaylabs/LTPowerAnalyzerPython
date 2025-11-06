#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Single Meter Efficiency Example

This script demonstrates how to perform efficiency measurements using a single 
RL2000 meter. It performs a current sweep and calculates efficiency between 
input and output power measurements.

Usage:
    python SingleMeterEfficiency.py

Requirements:
    - RL2000 hardware connected to the system
    - Serial communication drivers installed

History:
    07-13-2025  v1.0.0 - Initial version
    10-13-2025  v1.0.1 - Updated header and import paths
"""

import sys
import os

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.RL2000Driver import RL2000
from datetime import datetime
import asyncio
import csv

#RL2000 driver global variable
device_name = "RL2000" 
device = RL2000(device_name)
device.debug = False     

async def main():
    try:
        #sweep file name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        sweep_file_name = f"efficiency_sweep_{timestamp}.csv"

        #sweep variables
        current_load_start = 1e-3
        current_load_end = 10
        current_load_points_per_decade = 18
        current_load_device_index = 0
        current_load_scale = "log"
        servo_voltage = 12.0
        servo_voltmeter = 0
        sample_rate = 3 # 0 = slowest, 3 = fastest

        # Open the RL2000
        device.open_all_devices()
        if (device.port_ok):

            #open the file in the same directory as the script
            script_dir = os.path.dirname(os.path.realpath(__file__))
            file_path = os.path.join(script_dir, sweep_file_name)
            with open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file)

                #clear any existing errors
                device.clear_errors()

                if (current_load_scale == "log"):
                    current_values = device.get_decade_value_list(current_load_start, current_load_end, current_load_points_per_decade)
                else:
                    current_values = device.get_linear_value_list(current_load_start, current_load_end, current_load_points_per_decade)

                #Disable the automatic system check that would be run after each command
                #in order to speed up the sweep
                await device.disable_all_automatic_system_check()

                #set the sample rate
                await device.set_all_sample_rates(sample_rate)

                # Print header
                header = ["I1 (A)","V1 (V)","P1 (W)","I2 (A)","V2 (V)","P2 (W)","Efficiency (%)", "Ploss (W)"]
                print("\t".join(header))
                writer.writerow(header)

                #set the current load
                for current in current_values:

                    #set the current load
                    device.set_current_load(current_load_device_index,current)
            
                    #execute system check to autorange current meters
                    await device.execute_all_system_check()

                    #servo input
                    voltage_channel = 0
                    await device.set_all_servo_voltages([servo_voltage], [servo_voltmeter])
                    #device.set_servo_voltage(voltage_channel,servo_voltage,servo_voltmeter)
                    await device.delay_milliseconds(10)

                    # Read all current and voltages asynchronously
                    values = await device.read_all_current_and_voltage()
                    
                    # Print values in a single line per measurement
                    for measurement in values:
                        efficiency = 100* measurement.Power[1] / measurement.Power[0] if measurement.Power[0] != 0 else 0
                        power_loss = measurement.Power[0] - measurement.Power[1]
                        sweep_data = [
                            f"{measurement.Current[0]:.3E}", f"{measurement.Voltage[0]:.4f}", f"{measurement.Power[0]:.3f}",
                            f"{measurement.Current[1]:.3E}", f"{measurement.Voltage[1]:.4f}", f"{measurement.Power[1]:.3f}",
                            f"{efficiency:.2f}", f"{power_loss:.3f}"
                        ]
                        print("\t".join(sweep_data))
                        writer.writerow(sweep_data)

                    if (device.error != 0):
                        error_description = device.error_description
                        error_device_index = device.error_device_index + 1
                        print(f"Error on Meter {error_device_index}: {error_description}")
                        break

                #reset the current
                device.set_current_load(current_load_device_index,0)

                # Read all temperatures asynchronously
                temperatures = await device.read_all_temperatures()

                # Iterate through each temperature string
                for temp in temperatures:
                    # Print the temperatures
                    print(f"\nCurrent Meter Temp: {temp[0]}°C, Current Load Temp: {temp[1]}°C")

                #Enable the automatic system check again
                await device.enable_all_automatic_system_check()

    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {e}")

    finally:
        #close the device
        device.close()
        print("\nProgram Complete\n")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())        