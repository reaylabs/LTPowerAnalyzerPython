#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LNAmplifier EEPROM Data Read Test with Frequency Response Analysis

This script demonstrates reading calibration data from LNAmplifier EEPROM
using the high-level get_eeprom_dataset function. It connects to the LNAmplifier
device and reads frequency and gain datasets from specific EEPROM data indices.

The script reads:
- Frequency data from data_index 0
- Filter 1 gain data from data_index 1  
- Filter 2 gain data from data_index 2
- Filter 3 gain data from data_index 3
- Filter 4 gain data from data_index 4
- Filter 5 gain data from data_index 5
- Filter 6 gain data from data_index 6
- Filter 7 gain data from data_index 7
- Filter 8 gain data from data_index 8

Output:
- Creates a single CSV file with columns: Frequency_Hz, Filter1_Gain_dB, Filter2_Gain_dB, Filter3_Gain_dB, Filter4_Gain_dB, Filter5_Gain_dB, Filter6_Gain_dB, Filter7_Gain_dB, Filter8_Gain_dB
- Each row contains one frequency point with corresponding gains for all eight filters
- Missing data is marked as "N/A" in the CSV
- Displays Frequency Response Analysis Summary with performance metrics and bandwidth measurements

Analysis Features:
- Gain statistics (min, max, mean, range) for each filter
- Gain flatness analysis (maximum deviation, RMS deviation)
- Bandwidth measurements (-1dB and -3dB bandwidth)
- Comparative summary table for easy filter performance comparison

Usage:
    python ReadEEPROMDataTest.py

Requirements:
    - LNAmplifier device connected via serial port
    - Calibration data previously stored in EEPROM

History:
    10-20-2025  v1.0.0 - Initial EEPROM read test version with CSV output
    10-21-2025  v1.1.0 - Added comprehensive frequency response analysis with summary tables
"""

import sys
import os
import time
import math
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.append(project_root)
sys.path.append(drivers_dir)

from Drivers.LNAmplifierDriver import LNAmplifier

def save_dataset_to_file(data, filename, data_name):
    """
    Save dataset to a text file.
    
    Args:
        data (list): Array of float values
        filename (str): Output filename
        data_name (str): Description of the data
    """
    try:
        with open(filename, 'w') as f:
            f.write(f"# {data_name}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Count: {len(data)} values\n")
            f.write("#\n")
            
            for i, value in enumerate(data):
                f.write(f"{i:4d}: {value:.6f}\n")
        
        print(f"✓ {data_name} saved to: {filename}")
    except Exception as e:
        print(f"✗ Failed to save {data_name}: {e}")

def plot_filter_gains(frequencies, gain1, gain2, gain3, gain4, gain5, gain6, gain7, gain8, data_dir, timestamp):
    """
    Create a plot of the eight filter gains vs frequency.
    
    Args:
        frequencies (list): Array of frequency values in Hz
        gain1 (list): Filter 1 gain data in dB
        gain2 (list): Filter 2 gain data in dB  
        gain3 (list): Filter 3 gain data in dB
        gain4 (list): Filter 4 gain data in dB
        gain5 (list): Filter 5 gain data in dB
        gain6 (list): Filter 6 gain data in dB
        gain7 (list): Filter 7 gain data in dB
        gain8 (list): Filter 8 gain data in dB
        data_dir (str): Directory to save the plot
        timestamp (str): Timestamp for filename
    """
    try:
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Convert frequencies to MHz for better readability
        freq_mhz = [f / 1e6 for f in frequencies]
        
        # Plot each filter's gain
        if gain1 is not None:
            plt.plot(freq_mhz, gain1, 'b.-', linewidth=2, markersize=4, label='Filter 1', alpha=0.8)
        if gain2 is not None:
            plt.plot(freq_mhz, gain2, 'r.-', linewidth=2, markersize=4, label='Filter 2', alpha=0.8)
        if gain3 is not None:
            plt.plot(freq_mhz, gain3, 'g.-', linewidth=2, markersize=4, label='Filter 3', alpha=0.8)
        if gain4 is not None:
            plt.plot(freq_mhz, gain4, 'm.-', linewidth=2, markersize=4, label='Filter 4', alpha=0.8)
        if gain5 is not None:
            plt.plot(freq_mhz, gain5, 'c.-', linewidth=2, markersize=4, label='Filter 5', alpha=0.8)
        if gain6 is not None:
            plt.plot(freq_mhz, gain6, 'y.-', linewidth=2, markersize=4, label='Filter 6', alpha=0.8)
        if gain7 is not None:
            plt.plot(freq_mhz, gain7, 'k.-', linewidth=2, markersize=4, label='Filter 7', alpha=0.8)
        if gain8 is not None:
            plt.plot(freq_mhz, gain8, 'tab:orange', linewidth=2, markersize=4, label='Filter 8', alpha=0.8)
        
        # Set labels and title
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Gain (dB)')
        plt.title('LNAmplifier Filter Gains vs Frequency')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='lower left')
        
        # Set log scale for frequency if frequency range is large
        freq_range = max(frequencies) / min(frequencies)
        if freq_range > 100:  # Use log scale if frequency spans more than 2 decades
            plt.semilogx()
        
        # Add text box with measurement info (positioned to avoid legend overlap)
        info_text = f"Frequency Range: {min(frequencies):.1f} Hz - {max(frequencies)/1e6:.3f} MHz\n"
        info_text += f"Data Points: {len(frequencies)}\n"
        info_text += f"Generated: {timestamp.replace('_', ' ')}"
        
        plt.text(0.35, 0.02, info_text, transform=plt.gca().transAxes,
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                fontsize=9)
        
        plt.tight_layout()
        
        # Save the plot
        plot_filename = f"eeprom_filter_gains_{timestamp}.png"
        plot_full_path = os.path.join(data_dir, plot_filename)
        plt.savefig(plot_full_path, dpi=300, bbox_inches='tight')
        
        # Show the plot
        plt.show()
        
        print(f"✓ Plot saved: {plot_filename}")
        print(f"  Path: {plot_full_path}")
        
    except Exception as e:
        print(f"✗ Failed to create plot: {e}")

def main():
    """Main function to read EEPROM datasets."""
    
    print("LNAmplifier EEPROM Data Read Test")
    print("=" * 40)
    
    # Initialize LNAmplifier device
    lna_device = None
    port_index = 0  # Use first available port
    
    try:
        # Connect to LNAmplifier using same logic as other examples
        print("--- Connecting to LNAmplifier ---")
        device_name = "LNAmplifier"
        lna_device = LNAmplifier(device_name)
        lna_device.debug = False  # Set to True for detailed debug output
        
        print("Searching for LNAmplifier device...")
        lna_device.open_all_devices(print_status=False)
        
        # Check if at least one device was successfully opened
        if lna_device.port_count > 0 and lna_device.port_ok(0):
            print("✓ LNAmplifier connected successfully")
            
            # Use only the first device (port index 0)
            port_index = 0
            lna_device.clear_errors()
            
            print(f"Using Device 1 (Port {port_index})")
        else:
            print("✗ No LNAmplifier device found")
            print("Please check:")
            print("  - Device is connected via USB/Serial")
            print("  - Device is powered on")
            print("  - Correct drivers are installed")
            return
        
        # Display current device configuration
        print(f"\n--- Device Configuration ---")
        point_count = lna_device.get_point_count(port_index)
        current_filter = lna_device.get_filter(port_index)
        
        print(f"Point Count: {point_count}")
        print(f"Current Filter: {current_filter}")
        
        # Read datasets from EEPROM
        print(f"\n--- Reading EEPROM Datasets ---")
        
        datasets = {}
        dataset_info = [
            (0, "Frequency Data"),
            (1, "Filter 1 Gain Data"),
            (2, "Filter 2 Gain Data"),
            (3, "Filter 3 Gain Data"),
            (4, "Filter 4 Gain Data"),
            (5, "Filter 5 Gain Data"),
            (6, "Filter 6 Gain Data"),
            (7, "Filter 7 Gain Data"),
            (8, "Filter 8 Gain Data")
        ]
        
        # Read each dataset
        for data_index, data_name in dataset_info:
            print(f"\nReading {data_name} from data_index_{data_index}...")
            
            start_time = time.time()
            dataset = lna_device.get_eeprom_dataset(data_index, port_index)
            read_time = time.time() - start_time
            
            if dataset is not None:
                datasets[data_index] = dataset
                print(f"✓ Successfully read {len(dataset)} values in {read_time:.3f} seconds")
            else:
                datasets[data_index] = None
                print(f"✗ Failed to read {data_name}")
                # Add debug info for missing data
                if data_index == 4:
                    print("  Note: Filter 4 data may not be available in EEPROM")
                    print("  This is normal if only 3 filters were calibrated")
        
        # Check for data consistency
        print(f"\n--- Data Consistency Check ---")
        frequency_data = datasets[0]
        
        if frequency_data is not None:
            expected_count = len(frequency_data)
            print(f"Expected data count (based on frequency): {expected_count}")
            
            for data_index in [1, 2, 3, 4, 5, 6, 7, 8]:
                gain_data = datasets[data_index]
                if gain_data is not None:
                    if len(gain_data) == expected_count:
                        print(f"✓ Filter {data_index} data length matches ({len(gain_data)} values)")
                    else:
                        print(f"⚠ Filter {data_index} data length mismatch: expected {expected_count}, got {len(gain_data)}")
                else:
                    print(f"✗ Filter {data_index} data not available")
        
        # Save datasets to CSV file
        print(f"\n--- Saving Data to CSV File ---")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "Data")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Create Data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Create CSV file with all data
        csv_filename = f"eeprom_calibration_data_{timestamp}.csv"
        csv_full_path = os.path.join(data_dir, csv_filename)
        
        try:
            # Check if we have all required datasets
            frequencies = datasets[0]  # data_index 0
            gain1 = datasets[1]       # data_index 1 (Filter 1)
            gain2 = datasets[2]       # data_index 2 (Filter 2) 
            gain3 = datasets[3]       # data_index 3 (Filter 3)
            gain4 = datasets[4]       # data_index 4 (Filter 4)
            gain5 = datasets[5]       # data_index 5 (Filter 5)
            gain6 = datasets[6]       # data_index 6 (Filter 6)
            gain7 = datasets[7]       # data_index 7 (Filter 7)
            gain8 = datasets[8]       # data_index 8 (Filter 8)
            
            if frequencies is not None:
                with open(csv_full_path, 'w', newline='') as csvfile:
                    # Write header
                    csvfile.write("# LNAmplifier EEPROM Calibration Data\n")
                    csvfile.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    csvfile.write(f"# Point Count: {len(frequencies)}\n")
                    csvfile.write("#\n")
                    csvfile.write("Frequency_Hz,Filter1_Gain_dB,Filter2_Gain_dB,Filter3_Gain_dB,Filter4_Gain_dB,Filter5_Gain_dB,Filter6_Gain_dB,Filter7_Gain_dB,Filter8_Gain_dB\n")
                    
                    # Write data rows
                    for i in range(len(frequencies)):
                        freq = frequencies[i]
                        g1 = gain1[i] if gain1 is not None and i < len(gain1) else "N/A"
                        g2 = gain2[i] if gain2 is not None and i < len(gain2) else "N/A"
                        g3 = gain3[i] if gain3 is not None and i < len(gain3) else "N/A"
                        g4 = gain4[i] if gain4 is not None and i < len(gain4) else "N/A"
                        g5 = gain5[i] if gain5 is not None and i < len(gain5) else "N/A"
                        g6 = gain6[i] if gain6 is not None and i < len(gain6) else "N/A"
                        g7 = gain7[i] if gain7 is not None and i < len(gain7) else "N/A"
                        g8 = gain8[i] if gain8 is not None and i < len(gain8) else "N/A"
                        
                        csvfile.write(f"{freq:.6f},{g1},{g2},{g3},{g4},{g5},{g6},{g7},{g8}\n")
                
                print(f"✓ CSV file saved: {csv_filename}")
                print(f"  Path: {csv_full_path}")
                
                # Report what data was included
                data_status = []
                if frequencies is not None:
                    data_status.append(f"Frequencies: {len(frequencies)} points")
                if gain1 is not None:
                    data_status.append(f"Filter 1 gains: {len(gain1)} points")
                if gain2 is not None:
                    data_status.append(f"Filter 2 gains: {len(gain2)} points")  
                if gain3 is not None:
                    data_status.append(f"Filter 3 gains: {len(gain3)} points")
                if gain4 is not None:
                    data_status.append(f"Filter 4 gains: {len(gain4)} points")
                if gain5 is not None:
                    data_status.append(f"Filter 5 gains: {len(gain5)} points")
                if gain6 is not None:
                    data_status.append(f"Filter 6 gains: {len(gain6)} points")
                if gain7 is not None:
                    data_status.append(f"Filter 7 gains: {len(gain7)} points")
                if gain8 is not None:
                    data_status.append(f"Filter 8 gains: {len(gain8)} points")
                
                print(f"  Included data: {', '.join(data_status)}")
                
                # Create plot of filter gains vs frequency
                print(f"\n--- Creating Filter Gains Plot ---")
                plot_filter_gains(frequencies, gain1, gain2, gain3, gain4, gain5, gain6, gain7, gain8, data_dir, timestamp)
                
            else:
                print("✗ Cannot create CSV: No frequency data available")
                
        except Exception as e:
            print(f"✗ Failed to create CSV file: {e}")
        
        # Display frequency response analysis summary
        frequencies = datasets[0]  # data_index 0
        
        if frequencies is not None:
            print(f"\n--- Frequency Response Analysis Summary ---")
            
            # Analyze each filter dataset
            filter_analyses = []
            
            for filter_num in range(1, 9):  # Filters 1, 2, 3, 4, 5, 6, 7, 8
                gain_data = datasets[filter_num]  # data_index 1, 2, 3, 4, 5, 6, 7, 8
                
                if gain_data is not None:
                    # Basic statistics
                    min_gain = min(gain_data)
                    max_gain = max(gain_data)
                    mean_gain = sum(gain_data) / len(gain_data)
                    gain_range = max_gain - min_gain
                    
                    # Calculate gain flatness (deviation from mean)
                    gain_deviations = [abs(gain - mean_gain) for gain in gain_data]
                    max_deviation = max(gain_deviations)
                    rms_deviation = math.sqrt(sum(dev**2 for dev in gain_deviations) / len(gain_deviations))
                    
                    # Find -3dB bandwidth (relative to max gain)
                    gain_3db_threshold = max_gain - 3.0
                    frequencies_above_3db = []
                    
                    for i, gain in enumerate(gain_data):
                        if gain >= gain_3db_threshold:
                            frequencies_above_3db.append(frequencies[i])
                    
                    bandwidth_3db = None
                    if len(frequencies_above_3db) >= 2:
                        bandwidth_3db = max(frequencies_above_3db) - min(frequencies_above_3db)
                    
                    # Find -1dB bandwidth (relative to max gain) 
                    gain_1db_threshold = max_gain - 1.0
                    frequencies_above_1db = []
                    
                    for i, gain in enumerate(gain_data):
                        if gain >= gain_1db_threshold:
                            frequencies_above_1db.append(frequencies[i])
                    
                    bandwidth_1db = None
                    if len(frequencies_above_1db) >= 2:
                        bandwidth_1db = max(frequencies_above_1db) - min(frequencies_above_1db)
                    
                    # Store analysis for summary table
                    filter_analyses.append({
                        'filter_num': filter_num,
                        'min_gain': min_gain,
                        'max_gain': max_gain,
                        'mean_gain': mean_gain,
                        'gain_range': gain_range,
                        'max_deviation': max_deviation,
                        'rms_deviation': rms_deviation,
                        'bandwidth_1db': bandwidth_1db,
                        'bandwidth_3db': bandwidth_3db
                    })
            
            # Display summary table if we have filter data
            if filter_analyses:
                print(f"\nFrequency Range: {min(frequencies):.1f} Hz to {max(frequencies)/1e6:.3f} MHz")
                # Get data points from the first available filter data
                first_available_filter = next((analysis for analysis in filter_analyses), None)
                if first_available_filter:
                    filter_num = first_available_filter['filter_num']
                    filter_data = datasets[filter_num]
                    print(f"Data Points: {len(filter_data)} per filter")
                
                # Create summary table
                print(f"\n{'Metric':<20} ", end="")
                for analysis in filter_analyses:
                    print(f"Filter {analysis['filter_num']:<10}", end="")
                print()
                print("-" * (20 + 15 * len(filter_analyses)))
                
                # Key performance metrics
                metrics = [
                    ('Max Gain (dB)', 'max_gain', '.2f'),
                    ('Min Gain (dB)', 'min_gain', '.2f'),
                    ('Mean Gain (dB)', 'mean_gain', '.2f'),
                    ('Gain Range (dB)', 'gain_range', '.2f'),
                    ('Max Dev (dB)', 'max_deviation', '.3f'),
                    ('RMS Dev (dB)', 'rms_deviation', '.3f'),
                ]
                
                for metric_name, key, fmt in metrics:
                    print(f"{metric_name:<20} ", end="")
                    for analysis in filter_analyses:
                        value = analysis.get(key)
                        if value is not None:
                            formatted_value = f"{value:{fmt}}"
                            print(f"{formatted_value:<15}", end="")
                        else:
                            print(f"{'N/A':<15}", end="")
                    print()
                
                # Bandwidth metrics
                print(f"\n{'Bandwidth':<20} ", end="")
                for analysis in filter_analyses:
                    print(f"Filter {analysis['filter_num']:<10}", end="")
                print()
                print("-" * (20 + 15 * len(filter_analyses)))
                
                bw_metrics = [
                    ('-1dB BW (MHz)', 'bandwidth_1db'),
                    ('-3dB BW (MHz)', 'bandwidth_3db'),
                ]
                
                for metric_name, key in bw_metrics:
                    print(f"{metric_name:<20} ", end="")
                    for analysis in filter_analyses:
                        value = analysis.get(key)
                        if value is not None:
                            print(f"{value/1e6:.2f}{'':>10}", end="")
                        else:
                            print(f"{'N/A':<15}", end="")
                    print()
                    
            else:
                print("✗ No gain data available for analysis")
        
        else:
            print(f"\n✗ Cannot perform frequency response analysis: No frequency data available")
        
        print(f"\n✓ EEPROM read test completed successfully")
        
    except Exception as e:
        print(f"✗ Error during EEPROM read test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up connection
        print(f"\n--- Cleanup ---")
        
        if lna_device and lna_device.port_count > 0:
            try:
                print("Disconnecting from LNAmplifier...", end=" ")
                lna_device.close()
                print("✓")
            except Exception as e:
                print(f"✗ Error disconnecting LNAmplifier: {e}")
        
        print("EEPROM read test completed")

if __name__ == "__main__":
    main()
