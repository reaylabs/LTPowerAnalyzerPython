#!/usr/bin/env python3
"""
LTpowerAnalyzer Transient Measurement Example

This script demonstrates how to use the transient measurement functionality
of the LTpowerAnalyzer Python driver.

Features demonstrated:
- Device connection and setup
- Transient measurement configuration
- PWL (Piece-Wise Linear) transient measurements
- Data acquisition and analysis
- Trigger setup for transient measurements

Requirements:
- LTpowerAnalyzer hardware connected
- LTpowerAnalyzer software installed
- Current probe connected

Author: Analog Devices, Inc.
License: See LICENSE.txt
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# Add the Drivers directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
drivers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'Drivers')
sys.path.append(drivers_dir)

from LTpowerAnalyzerDriver import LTpowerAnalyzer

def main():
    """Main function demonstrating transient measurements"""
    
    # Initialize the LTpowerAnalyzer with debug enabled
    analyzer = LTpowerAnalyzer(debug=True)
    
    print("=" * 60)
    print("LTpowerAnalyzer Transient Measurement Example")
    print("=" * 60)
    
    # Connect to the device
    print("\n1. Connecting to LTpowerAnalyzer...")
    if not analyzer.connect():
        print("Failed to connect to LTpowerAnalyzer. Please check connections.")
        return
    
    print("Successfully connected to LTpowerAnalyzer!")
    
    # Display current probe information
    print("\\n2. Checking current probe information...")
    probe_info = analyzer.get_current_probe_info()
    if probe_info['connected']:
        print(f"Current probe detected: {probe_info['name']}")
        print(f"  Probe Type: {probe_info['type']}")
        print(f"  Max Current: {probe_info['max_current']:.1f} A")
        print(f"  Max DC Current: {probe_info['max_dc_current']:.1f} A") 
        print(f"  Temperature: {probe_info['temperature']:.1f}°C")
        print(f"  Status: {'⚠️ Error' if probe_info['error'] else '✅ OK'}")
        
        if probe_info['error']:
            print("⚠️  Warning: Current probe has an error condition!")
            
        if probe_info['max_current'] < 1.0:
            print(f"⚠️  Note: Using {probe_info['type']} probe - ensure test currents are within limits")
    else:
        print("❌ No current probe detected!")
        print("Please connect a current probe before running transient measurements.")
        analyzer.disconnect()
        return
    
    # Initialize transient measurement
    print("\\n3. Initializing transient measurement...")
    if not analyzer.initialize_transient_measurement():
        print("Failed to initialize transient measurement.")
        analyzer.disconnect()
        return
    
    print("Transient measurement initialized successfully!")
    
    # Example 1: Simple step transient measurement
    print("\n3. Example 1: Step Transient Measurement")
    step_transient_example(analyzer)
    
    # Example 2: PWL transient measurement  
    print("\n4. Example 2: PWL Transient Measurement")
    pwl_transient_example(analyzer)
    
    # Example 3: Pulse train transient measurement
    print("\n5. Example 3: Pulse Train Transient Measurement")  
    pulse_train_example(analyzer)
    
    # Disconnect
    print("\n6. Disconnecting...")
    analyzer.disconnect()
    print("Disconnected successfully!")

def step_transient_example(analyzer):
    """Demonstrate a simple step transient measurement"""
    
    # Get probe information to determine safe current levels
    probe_info = analyzer.get_current_probe_info()
    max_safe_current = probe_info['max_current'] * 0.8  # Use 80% of max current for safety
    
    # Configure transient measurement parameters
    transient_config = LTpowerAnalyzer.TransientSetup(
        current1=0.0,              # Low current: 0A
        current2=min(0.5, max_safe_current),  # High current: 0.5A or 80% of probe max, whichever is lower
        pulse_width=1e-3,          # Pulse width: 1ms
        pulse_count=1,             # Single pulse
        duty_cycle=0.1,            # 10% duty cycle
        rise_time=1e-6,            # Rise time: 1μs
        fall_time=1e-6,            # Fall time: 1μs
        acquisition_time=10e-3,    # Acquisition time: 10ms
        measure_switching_frequency=False
    )
    
    # Configure trigger
    trigger_level = transient_config.current2 / 2.0  # Half of maximum current
    trigger_config = LTpowerAnalyzer.TriggerSetup(
        channel=1,                 # Trigger on current (not voltage)
        level=trigger_level,       # Trigger level: half of max current
        delay=0.0,                 # No delay
        timeout=1.0,               # 1 second timeout
        slope=0,                   # Rising edge
        auto=True                  # Auto trigger mode
    )
    
    print("  Configured step transient measurement:")
    print(f"    Current step: {transient_config.current1}A -> {transient_config.current2:.3f}A")
    print(f"    Probe max current: {probe_info['max_current']:.1f}A ({probe_info['type']} probe)")
    print(f"    Pulse width: {transient_config.pulse_width*1000:.1f}ms")
    print(f"    Acquisition time: {transient_config.acquisition_time*1000:.1f}ms")
    
    # Execute the measurement
    print("  Executing step transient measurement...")
    success = analyzer.execute_transient_measurement(transient_config, trigger_config)
    
    if success:
        print("  Step transient measurement completed successfully!")
        
        # Get the measurement data
        input_data = analyzer.transient_input_data
        output_data = analyzer.transient_output_data
        time_array = analyzer.get_transient_time_array()
        
        if input_data is not None and output_data is not None:
            print(f"  Captured {len(input_data)} samples at {analyzer.transient_sample_frequency/1e6:.1f} MSa/s")
            
            # Save data to CSV
            save_transient_data_csv("step_transient", time_array, input_data, output_data)
            
            # Plot the results if matplotlib is available
            try:
                plot_transient_results("Step Transient", time_array, input_data, output_data)
            except ImportError:
                print("  Matplotlib not available for plotting.")
        else:
            print("  Warning: No measurement data available.")
    else:
        print("  Step transient measurement failed!")

def pwl_transient_example(analyzer):
    """Demonstrate a PWL (Piece-Wise Linear) transient measurement"""
    
    # Get probe information to determine safe current levels
    probe_info = analyzer.get_current_probe_info()
    max_safe_current = probe_info['max_current'] * 0.8  # Use 80% of max current for safety
    
    # Create a custom PWL current profile - a triangular wave
    acquisition_time = 20e-3  # 20ms acquisition time
    
    peak_current = min(0.8, max_safe_current)  # Use smaller of 0.8A or 80% of probe max
    mid_current = min(0.2, max_safe_current * 0.25)  # Use 25% of probe max or 0.2A
    
    pwl_points = [
        LTpowerAnalyzer.PWLPoint(0.0e-3, 0.0),         # Start at 0A
        LTpowerAnalyzer.PWLPoint(2.5e-3, 0.0),         # Stay at 0A for 2.5ms
        LTpowerAnalyzer.PWLPoint(5.0e-3, peak_current), # Ramp to peak current at 5ms
        LTpowerAnalyzer.PWLPoint(10.0e-3, peak_current),# Hold at peak current until 10ms
        LTpowerAnalyzer.PWLPoint(15.0e-3, mid_current), # Drop to mid current at 15ms
        LTpowerAnalyzer.PWLPoint(20.0e-3, 0.0)         # Return to 0A at 20ms
    ]
    
    # Configure trigger
    trigger_level = peak_current / 2.0  # Half of maximum current
    trigger_config = LTpowerAnalyzer.TriggerSetup(
        channel=1,                 # Trigger on current (not voltage)
        level=trigger_level,       # Trigger level: half of max current
        delay=0.0,                 # No delay
        timeout=2.0,               # 2 second timeout
        slope=0,                   # Rising edge
        auto=True                  # Auto trigger mode
    )
    
    print("  Configured PWL transient measurement:")
    print(f"    PWL points: {len(pwl_points)} segments")
    print(f"    Acquisition time: {acquisition_time*1000:.1f}ms")
    print(f"    Current range: 0A -> {peak_current:.3f}A -> {mid_current:.3f}A -> 0A")
    print(f"    Probe max current: {probe_info['max_current']:.1f}A ({probe_info['type']} probe)")
    print(f"    Trigger: Current rising edge at {trigger_level:.3f}A (50% of max current)")
    
    # Execute the PWL measurement
    print("  Executing PWL transient measurement...")
    success = analyzer.execute_pwl_transient_measurement(
        pwl_points, 
        acquisition_time, 
        trigger_config, 
        measure_switching_frequency=False
    )
    
    if success:
        print("  PWL transient measurement completed successfully!")
        
        # Get the measurement data
        input_data = analyzer.transient_input_data
        output_data = analyzer.transient_output_data
        time_array = analyzer.get_transient_time_array()
        
        if input_data is not None and output_data is not None:
            print(f"  Captured {len(input_data)} samples at {analyzer.transient_sample_frequency/1e6:.1f} MSa/s")
            
            # Save data to CSV
            save_transient_data_csv("pwl_transient", time_array, input_data, output_data)
            
            # Plot the results
            try:
                plot_transient_results("PWL Transient", time_array, input_data, output_data)
            except ImportError:
                print("  Matplotlib not available for plotting.")
        else:
            print("  Warning: No measurement data available.")
    else:
        print("  PWL transient measurement failed!")

def pulse_train_example(analyzer):
    """Demonstrate a pulse train using the PWL utility function"""
    
    # Get probe information to determine safe current levels
    probe_info = analyzer.get_current_probe_info()
    max_safe_current = probe_info['max_current'] * 0.8  # Use 80% of max current for safety
    
    low_current = min(0.1, max_safe_current * 0.125)  # 12.5% of probe max or 0.1A
    high_current = min(0.6, max_safe_current)         # 80% of probe max or 0.6A
    
    # Create a pulse train using the utility function
    pwl_points = analyzer.create_pwl_pulse_train(
        current_low=low_current,   # Low current
        current_high=high_current, # High current  
        pulse_width=1e-3,          # Pulse width: 1ms
        period=4e-3,               # Period: 4ms (25% duty cycle)
        num_pulses=3               # 3 pulses
    )
    
    acquisition_time = 15e-3      # 15ms acquisition time
    
    # Configure trigger
    trigger_level = high_current / 2.0  # Half of maximum current
    trigger_config = LTpowerAnalyzer.TriggerSetup(
        channel=1,                 # Trigger on current (not voltage)
        level=trigger_level,       # Trigger level: half of max current
        delay=0.0,                 # No delay
        timeout=2.0,               # 2 second timeout
        slope=0,                   # Rising edge
        auto=True                  # Auto trigger mode
    )
    
    print("  Configured pulse train measurement:")
    print(f"    Pulse current: {low_current:.3f}A -> {high_current:.3f}A")
    print(f"    Probe max current: {probe_info['max_current']:.1f}A ({probe_info['type']} probe)")
    print(f"    Pulse width: {1e-3*1000:.1f}ms")
    print(f"    Period: {4e-3*1000:.1f}ms")
    print(f"    Number of pulses: {3}")
    print(f"    Trigger: Current rising edge at {trigger_level:.3f}A (50% of max current)")
    
    # Execute the pulse train measurement
    print("  Executing pulse train measurement...")
    success = analyzer.execute_pwl_transient_measurement(
        pwl_points,
        acquisition_time, 
        trigger_config,
        measure_switching_frequency=False
    )
    
    if success:
        print("  Pulse train measurement completed successfully!")
        
        # Get the measurement data
        input_data = analyzer.transient_input_data
        output_data = analyzer.transient_output_data
        time_array = analyzer.get_transient_time_array()
        
        if input_data is not None and output_data is not None:
            print(f"  Captured {len(input_data)} samples at {analyzer.transient_sample_frequency/1e6:.1f} MSa/s")
            
            # Save data to CSV
            save_transient_data_csv("pulse_train", time_array, input_data, output_data)
            
            # Plot the results
            try:
                plot_transient_results("Pulse Train", time_array, input_data, output_data)
            except ImportError:
                print("  Matplotlib not available for plotting.")
        else:
            print("  Warning: No measurement data available.")
    else:
        print("  Pulse train measurement failed!")

def save_transient_data_csv(test_name, time_array, input_data, output_data):
    """Save transient measurement data to CSV file"""
    try:
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{test_name}_transient_{timestamp}.csv"
        
        print(f"  Saving data to {filename}...")
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Time (s)', 'Input (V)', 'Output (V)'])
            
            # Write data
            for i in range(len(time_array)):
                writer.writerow([
                    time_array[i],
                    input_data[i] if i < len(input_data) else 0,
                    output_data[i] if i < len(output_data) else 0
                ])
        
        print(f"  Data saved successfully to {filename}")
        
    except Exception as e:
        print(f"  Error saving data: {e}")

def plot_transient_results(title, time_array, input_data, output_data):
    """Plot the transient measurement results"""
    
    # Convert time to milliseconds for better readability
    time_ms = time_array * 1000
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Plot input data (current)
    ax1.plot(time_ms, input_data, 'b-', linewidth=1.5, label='Current')
    ax1.set_ylabel('Input Current (A)')
    ax1.set_title(f'{title} - Input Current vs Time')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot output data (voltage)
    ax2.plot(time_ms, output_data, 'r-', linewidth=1.5, label='Voltage')
    ax2.set_ylabel('Output Voltage (V)')
    ax2.set_xlabel('Time (ms)')
    ax2.set_title(f'{title} - Output Voltage vs Time')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(f'{title.lower().replace(" ", "_")}_plot.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"  Plot saved as {title.lower().replace(' ', '_')}_plot.png")

if __name__ == "__main__":
    main()