#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LNAmplifier Noise Density Measurement with LTPowerAnalyzer

This script measures the noise density of the LNAmplifier device using the LTPowerAnalyzer.
It sets up the LNAmplifier filter configuration, reads calibration data from EEPROM,
and then performs noise density measurements across a specified frequency range.

Features:
- LNAmplifier filter selection and configuration
- EEPROM frequency and gain data reading
- FFT-based noise density analysis with averaging
- CSV file export with frequency and noise density data
- Console output with measurement summary statistics
- Automated trigger setup for consistent measurements

Measurement Parameters:
- Sample frequency: 5 MHz
- FFT averaging: 8 averages for noise floor reduction
- Frequency range: 10 Hz to 1 MHz (configurable)
- Sample size: 2^22 points for high resolution

Output:
- CSV file: frequency_Hz, input_noise_density_V_per_sqrtHz
- Console summary with statistics and frequency band analysis

Usage:
    python LNANoiseDensity.py

Requirements:
    - LTpowerAnalyzer device connected via USB
    - LNAmplifier device connected via serial port
    - Calibration data stored in LNAmplifier EEPROM

History:
    10-21-2025  v1.0.0 - Initial LNAmplifier noise density measurement script
"""

# Import libraries
import sys
import os
import time
import msvcrt
import math
import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob

# Add the root project directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.insert(0, project_root)

# Add drivers dir AFTER importing LTpowerAnalyzer to avoid circular import
from Drivers.LTpowerAnalyzerDriver import LTpowerAnalyzer
# Now add drivers dir so LNAmplifierDriver can find SerialDeviceDriver
sys.path.insert(0, drivers_dir)
from Drivers.LNAmplifierDriver import LNAmplifier


def extract_eeprom_data(csv_file_path):
    """
    Extract EEPROM calibration data from CSV file.
    Returns (eeprom_frequencies, eeprom_gains) or (None, None) if not found.
    """
    eeprom_frequencies = []
    eeprom_gains = []
    
    try:
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
            
        # Find the EEPROM data section
        eeprom_section = False
        for line in lines:
            line = line.strip()
            if "# EEPROM Calibration Data" in line:
                eeprom_section = True
                continue
            elif eeprom_section and line.startswith('#'):
                continue  # Skip header lines
            elif eeprom_section and not line.startswith('#') and ',' in line:
                # Parse EEPROM data
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        freq = float(parts[0])
                        gain = float(parts[1])
                        eeprom_frequencies.append(freq)
                        eeprom_gains.append(gain)
                    except ValueError:
                        continue
                        
        if eeprom_frequencies and eeprom_gains:
            return np.array(eeprom_frequencies), np.array(eeprom_gains)
        else:
            return None, None
            
    except Exception as e:
        print(f"Warning: Could not extract EEPROM data: {e}")
        return None, None

def extract_measurement_parameters(csv_file_path):
    """
    Extract measurement parameters from CSV file comments.
    """
    params = {}
    try:
        with open(csv_file_path, 'r') as file:
            for line in file:
                if line.startswith('#'):
                    if 'LNA Filter:' in line:
                        params['lna_filter'] = line.split('LNA Filter:')[1].strip()
                    elif 'Sample Frequency:' in line:
                        params['sample_frequency'] = line.split('Sample Frequency:')[1].strip()
                    elif 'FFT Averages:' in line:
                        params['fft_averages'] = line.split('FFT Averages:')[1].strip()
                    elif 'Sample Size:' in line:
                        params['sample_size'] = line.split('Sample Size:')[1].strip()
                    elif 'FFT Bin Size:' in line:
                        params['fft_bin_size'] = line.split('FFT Bin Size:')[1].strip()
                else:
                    break  # Stop when we reach data rows
    except Exception as e:
        print(f"Warning: Could not extract parameters: {e}")
    return params

def plot_noise_density(csv_file_path):
    """
    Create log-log plots of noise density vs frequency from the specified CSV file.
    """
    print(f"📊 Creating plots from: {os.path.basename(csv_file_path)}")
    
    try:
        # Extract measurement parameters from CSV comments
        params = extract_measurement_parameters(csv_file_path)
        
        # Extract EEPROM calibration data
        eeprom_frequencies, eeprom_gains = extract_eeprom_data(csv_file_path)
        
        # Load the CSV data, stopping at EEPROM section
        measurement_data = []
        with open(csv_file_path, 'r') as file:
            lines = file.readlines()
        
        # Find measurement data section (skip comments, stop at EEPROM section)
        header_found = False
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            elif not header_found and ',' in line and 'frequency' in line:
                # This is the header line
                header_found = True
                header = line.split(',')
                continue
            elif header_found and ',' in line and not line.startswith('#'):
                # Check if this line has 4 columns (measurement data) vs 2 columns (EEPROM data)
                parts = line.split(',')
                if len(parts) == 4:  # Measurement data has 4 columns
                    measurement_data.append(parts)
                elif len(parts) == 2:  # EEPROM data has 2 columns, stop here
                    break
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(measurement_data, columns=header)
        # Convert numeric columns
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"✓ Loaded {len(df)} measurement data points")
        
        # Extract data for plotting
        frequency = df.iloc[:, 0].values  # First column: Frequency (Hz)
        measured_noise = df.iloc[:, 1].values  # Second column: Measured Noise Density (V/√Hz)
        
        # Check if we have LNA input noise data (4th column)
        has_lna_input_noise = len(df.columns) >= 4 and not df.iloc[:, 3].isna().all()
        
        if has_lna_input_noise:
            lna_gain_db = df.iloc[:, 2].values  # Third column: LNA Gain (dB)
            lna_input_noise = df.iloc[:, 3].values  # Fourth column: LNA Input Noise Density (V/√Hz)
        
        # Remove any NaN or zero values for log plotting
        valid_indices = (frequency > 0) & (measured_noise > 0) & ~np.isnan(frequency) & ~np.isnan(measured_noise)
        
        frequency_clean = frequency[valid_indices]
        measured_noise_clean = measured_noise[valid_indices]
        
        if has_lna_input_noise:
            lna_input_noise_clean = lna_input_noise[valid_indices]
            lna_gain_db_clean = lna_gain_db[valid_indices]
        
        print(f"✓ {len(frequency_clean)} valid data points for plotting")
        
        # Create the plot
        if has_lna_input_noise:
            # Create subplot with three plots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14))
            
            # Create parameter text box
            param_text = []
            if 'lna_filter' in params:
                param_text.append(f"LNA Filter: {params['lna_filter']}")
            if 'sample_frequency' in params:
                param_text.append(f"Sample Freq: {params['sample_frequency']}")
            if 'fft_averages' in params:
                param_text.append(f"FFT Averages: {params['fft_averages']}")
            if 'sample_size' in params:
                param_text.append(f"Sample Size: {params['sample_size']}")
            if 'fft_bin_size' in params:
                param_text.append(f"FFT Bin Size: {params['fft_bin_size']}")
            
            param_string = '\n'.join(param_text)
            
            # Plot 1: Measured noise density
            ax1.loglog(frequency_clean, measured_noise_clean, 'b.-', linewidth=2, markersize=4, label='Measured Noise Density')
            ax1.set_xlabel('Frequency (Hz)')
            ax1.set_ylabel('Measured Noise Density (V/√Hz)')
            ax1.set_title('LNA Measured Noise Density vs Frequency')
            ax1.grid(True, which="both", ls="-", alpha=0.3)
            ax1.legend()
            
            # Add measurement parameters text box to first plot
            if param_text:
                ax1.text(0.98, 0.98, param_string, transform=ax1.transAxes, 
                        verticalalignment='top', horizontalalignment='right', 
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                        fontsize=9)
            
            # Plot 2: LNA input noise density (gain compensated)
            ax2.loglog(frequency_clean, lna_input_noise_clean, 'r.-', linewidth=2, markersize=4, label='LNA Input Noise Density')
            ax2.set_xlabel('Frequency (Hz)')
            ax2.set_ylabel('LNA Input Noise Density (V/√Hz)')
            ax2.set_title('LNA Input Noise Density vs Frequency (Gain Compensated)')
            ax2.grid(True, which="both", ls="-", alpha=0.3)
            ax2.legend()
            
            # Add measurement parameters text box to second plot
            if param_text:
                ax2.text(0.98, 0.98, param_string, transform=ax2.transAxes, 
                        verticalalignment='top', horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8),
                        fontsize=9)
            
            # Plot 3: LNA Gain vs Frequency
            if eeprom_frequencies is not None and eeprom_gains is not None:
                # Use EEPROM calibration data for gain plot
                ax3.semilogx(eeprom_frequencies, eeprom_gains, 'g.-', linewidth=2, markersize=4, label='LNA Gain (EEPROM)')
                ax3.set_xlabel('Frequency (Hz)')
                ax3.set_ylabel('LNA Gain (dB)')
                ax3.set_title('LNA Filter Gain vs Frequency (EEPROM Calibration Data)')
                ax3.grid(True, which="both", ls="-", alpha=0.3)
                ax3.legend()
                
                # Add measurement parameters text box to third plot
                if param_text:
                    ax3.text(0.98, 0.98, param_string, transform=ax3.transAxes, 
                            verticalalignment='top', horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8),
                            fontsize=9)
            else:
                # Fallback to measured gain data if EEPROM data not available
                ax3.semilogx(frequency_clean, lna_gain_db_clean, 'g.-', linewidth=2, markersize=4, label='LNA Gain (Measured)')
                ax3.set_xlabel('Frequency (Hz)')
                ax3.set_ylabel('LNA Gain (dB)')
                ax3.set_title('LNA Filter Gain vs Frequency (Measured Data)')
                ax3.grid(True, which="both", ls="-", alpha=0.3)
                ax3.legend()
                
                # Add measurement parameters text box to third plot
                if param_text:
                    ax3.text(0.98, 0.98, param_string, transform=ax3.transAxes, 
                            verticalalignment='top', horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8),
                            fontsize=9)
            
            plt.tight_layout()
            
        else:
            # Single plot for measured noise only
            plt.figure(figsize=(12, 8))
            plt.loglog(frequency_clean, measured_noise_clean, 'b.-', linewidth=2, markersize=4, label='Noise Density')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Noise Density (V/√Hz)')
            plt.title('Noise Density vs Frequency (Log-Log Scale)')
            plt.grid(True, which="both", ls="-", alpha=0.3)
            plt.legend()
        
        # Display statistics
        print(f"\n📈 Plot Statistics:")
        print(f"  Frequency range: {frequency_clean.min():.1f} Hz to {frequency_clean.max()/1e6:.3f} MHz")
        print(f"  Measured noise range: {measured_noise_clean.min():.2e} to {measured_noise_clean.max():.2e} V/√Hz")
        
        if has_lna_input_noise:
            print(f"  LNA input noise range: {lna_input_noise_clean.min():.2e} to {lna_input_noise_clean.max():.2e} V/√Hz")
            print(f"  LNA gain range: {lna_gain_db_clean.min():.1f} to {lna_gain_db_clean.max():.1f} dB")
        
        # Save the plot
        plot_filename = csv_file_path.replace('.csv', '_plot.png')
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"✓ Plot saved as: {os.path.basename(plot_filename)}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"❌ Error creating plot: {e}")
        import traceback
        traceback.print_exc()

try:
    # Program configuration
    debug = False
    display_results = False
    display_summary = False
    plot_results = True
    write_csv_file = True
    CSV_BASE_FILENAME = "LNANoiseDensity"  # Base filename for CSV output files

    #setup the measurement parameters
    sample_frequency = 5e6
    fft_average_count = 16
    point_count = 801
    sample_size = 2**22
    start_frequency = 10.0
    end_frequency = 1.0e6
    
    # LNAmplifier configuration
    lna_filter = 1  # Filter number (1, 2, or 3)
    data_index = lna_filter  # EEPROM data index matches filter number (1=Filter1, 2=Filter2, 3=Filter3)

    # Connect to LNAmplifier
    print("--- Connecting to LNAmplifier ---\n")
    device_name = "LNAmplifier"
    lna_device = LNAmplifier(device_name)
    lna_device.debug = False  # Set to True for debug output
    lna_device.open_all_devices(print_status=False)
    
    # Check if at least one device was successfully opened
    if lna_device.port_count > 0 and lna_device.port_ok(0):
        print("✓ LNAmplifier connected successfully")
        # Use only the first device (port index 0)
        port_index = 0
        lna_device.clear_errors()
    else:
        print("✗ No LNAmplifier device found")
        exit()

    # Set LNA filter
    print(f"Setting LNA filter to {lna_filter}...")
    try:
        lna_device.set_filter(str(lna_filter), port_index)
        print(f"✓ LNA filter set to {lna_filter}")
    except Exception as e:
        print(f"✗ Failed to set LNA filter: {e}")
        exit()
    
    # Read EEPROM frequency data (data_index 0)
    print("Reading EEPROM frequency data...")
    try:
        frequency_data = lna_device.get_eeprom_dataset(0, port_index)
        if frequency_data:
            print(f"✓ Read {len(frequency_data)} frequency points from EEPROM")
            print(f"  Range: {min(frequency_data):.1f} Hz to {max(frequency_data)/1e6:.3f} MHz")
        else:
            print("✗ No frequency data found in EEPROM")
            frequency_data = None
    except Exception as e:
        print(f"✗ Failed to read frequency data: {e}")
        frequency_data = None
    
    # Read EEPROM gain data for selected filter
    print(f"Reading EEPROM gain data for filter {lna_filter} (data_index {data_index})...")
    try:
        gain_data = lna_device.get_eeprom_dataset(data_index, port_index)
        if gain_data:
            print(f"✓ Read {len(gain_data)} gain points from EEPROM")
            print(f"  Range: {min(gain_data):.2f} dB to {max(gain_data):.2f} dB")
        else:
            print(f"✗ No gain data found for filter {lna_filter}")
            gain_data = None
    except Exception as e:
        print(f"✗ Failed to read gain data: {e}")
        gain_data = None

    # Connect to LTpowerAnalyzer
    print("\n--- LTpowerAnalyzer Setup ---")
    analyzer = LTpowerAnalyzer(debug)
    print("Connecting to LTpowerAnalyzer...")
    if not analyzer.connect():
        print("Failed to connect to LTpowerAnalyzer")
        exit()
    
    print(f"✓ Connected to LTpowerAnalyzer")
    print(f"Sample size max: {analyzer.sample_size_max}")
    analyzer.set_fft_window(3)
    print(f"FFT window: {analyzer.fft_window}")

    # Create trigger configuration
    trigger = LTpowerAnalyzer.TriggerSetup(
        channel=0,      # 0 = Output/Vout, 1 = Input/Current
        level=0.0,      # Trigger voltage level in volts
        delay=0.0,      # Trigger position/delay in seconds
        timeout=0.1,    # Auto-trigger timeout in seconds  
        slope=0,        # 0 = Rising, 1 = Falling, 2 = Either edge
        auto=True       # True = Auto mode, False = Normal mode
    )

    # Setup trigger before sampling
    analyzer.setup_trigger(trigger)

    # Setup sampling configuration
    sample_config = LTpowerAnalyzer.SampleSetup(
        sample_size=sample_size,         # Sample size (must be a power of 2)
        frequency= sample_frequency,            # Sample frequency in hertz
        fft_average_count= fft_average_count,      # Average count (must be a power of 2)
        gain_average_count= 1,      # Average count (must be a power of 2)
        filter_frequency=10000,     # Lowpass filter cutoff frequency in hertz
        filter_enable=False,        # Enable/disable lowpass filter
    )

    # Disable injection output
    analyzer.disable_injection_output()

    # Apply sampling configuration to meter
    analyzer.setup_gain_phase_measurement(sample_config)

    #Generate the test frequencies
    #test_frequencies = analyzer.generate_test_frequencies(50, 1, 6)
    test_frequencies = analyzer.bode100_log_points(start_frequency, end_frequency, point_count)
    # Store results
    results = []

    #add the column headers
    results.append(["FFT Frequency (Hz)", "Measured Noise Density (V/√Hz)", "LNA Gain (dB)", "LNA Input Noise Density (V/√Hz)"])
    analyzer.reset_averages()

    #Measure the noise density
    for j in range(fft_average_count):
        print(f"Executing gain and phase measurement {j+1} of {fft_average_count}")
        analyzer.execute_gain_phase_measurement()
        if msvcrt.kbhit():
            print("Key pressed, exiting...")
            break


    # add the results to the results list with unique frequencies
    print(f"\n--- Collecting Data from {len(test_frequencies)} test frequencies ---")
    used_bins = set()  # Track which FFT bins we've already used
    
    for i, signal_frequency in enumerate(test_frequencies):
        actual_bin_center_frequency, fft_bin = analyzer.get_closest_fft_frequency_and_bin(signal_frequency)
        
        # Only add if we haven't used this FFT bin before
        if fft_bin not in used_bins:
            measurement_frequency = analyzer.fft_frequency[fft_bin]
            measured_noise_density = analyzer.fft_input_noise_density[fft_bin]
            
            # Find the closest gain frequency and interpolate gain if needed
            if frequency_data and gain_data and len(frequency_data) == len(gain_data):
                # Interpolate gain between the two closest frequency points
                if measurement_frequency <= frequency_data[0]:
                    # Below the lowest calibration frequency, use the first point
                    gain_db = gain_data[0]
                elif measurement_frequency >= frequency_data[-1]:
                    # Above the highest calibration frequency, use the last point
                    gain_db = gain_data[-1]
                else:
                    # Find the two closest frequency points for interpolation
                    freq_differences = [(abs(f - measurement_frequency), i) for i, f in enumerate(frequency_data)]
                    freq_differences.sort()  # Sort by difference
                    
                    # Get the two closest indices
                    idx1 = freq_differences[0][1]
                    idx2 = freq_differences[1][1]
                    
                    # Ensure idx1 < idx2 for proper interpolation
                    if idx1 > idx2:
                        idx1, idx2 = idx2, idx1
                    
                    # Linear interpolation
                    f1, f2 = frequency_data[idx1], frequency_data[idx2]
                    g1, g2 = gain_data[idx1], gain_data[idx2]
                    
                    if f2 == f1:  # Avoid division by zero (should not happen with proper data)
                        gain_db = g1
                    else:
                        # Linear interpolation: g = g1 + (g2-g1) * (f-f1)/(f2-f1)
                        gain_db = g1 + (g2 - g1) * (measurement_frequency - f1) / (f2 - f1)
                
                # Convert gain from dB to linear scale
                gain_linear = 10**(gain_db / 20.0)
                
                # Calculate LNA input noise density (divide measured noise by gain)
                lna_input_noise_density = measured_noise_density / gain_linear
                
                # Store results: frequency, measured noise, gain (dB), LNA input noise
                results.append([measurement_frequency, measured_noise_density, gain_db, lna_input_noise_density])
                used_bins.add(fft_bin)
                
                if len(results) <= 6:  # Show first 5 data points for debugging (including header)
                    print(f"  Point {len(results)-1}: {measurement_frequency:.2f} Hz, Measured: {measured_noise_density:.2e} V/√Hz, Gain: {gain_db:.2f} dB, LNA Input: {lna_input_noise_density:.2e} V/√Hz")
            else:
                # No gain data available, just store measured noise
                results.append([measurement_frequency, measured_noise_density, None, None])
                used_bins.add(fft_bin)
                
                if len(results) <= 6:  # Show first 5 data points for debugging
                    print(f"  Point {len(results)-1}: {measurement_frequency:.2f} Hz, Measured: {measured_noise_density:.2e} V/√Hz (No gain data)")
    
    print(f"✓ Collected {len(results)-1} unique data points (excluding header)")
    
    # Debug: Check if we have data
    if len(results) <= 1:
        print("⚠ Warning: No data collected! Check measurement execution.")
    else:
        print(f"✓ Data collection successful: {len(results)-1} points")
    
    # Save results to CSV file
    print("\n--- Saving Data to CSV File ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "Data")
    
    # Create Data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_filename = f"{CSV_BASE_FILENAME}_{timestamp}.csv"
    csv_full_path = os.path.join(data_dir, csv_filename)
    
    try:
        with open(csv_full_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header with metadata
            csv_writer.writerow(["# LNAmplifier Noise Density Measurement"])
            csv_writer.writerow([f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            csv_writer.writerow([f"# LNA Filter: {lna_filter}"])
            csv_writer.writerow([f"# EEPROM Data Index: {data_index}"])
            csv_writer.writerow([f"# Sample Frequency: {sample_frequency/1e6:.1f} MHz"])
            csv_writer.writerow([f"# FFT Averages: {fft_average_count}"])
            csv_writer.writerow([f"# Sample Size: {sample_size} points"])
            csv_writer.writerow([f"# FFT Bin Size: {analyzer.fft_bin_size:.2f} Hz"])
            csv_writer.writerow([f"# Total Test Frequencies: {len(test_frequencies)}"])
            csv_writer.writerow([f"# Unique Data Points: {len(results)-1}"])
            if frequency_data:
                csv_writer.writerow([f"# EEPROM Frequency Points: {len(frequency_data)}"])
            if gain_data:
                csv_writer.writerow([f"# EEPROM Gain Points: {len(gain_data)}"])
            csv_writer.writerow(["#"])
            
            # Write column headers
            csv_writer.writerow(["frequency", "measured_noise_density", "lna_gain_db", "lna_input_noise_density"])
            
            # Write data rows (skip the original header row from results)
            data_rows_written = 0
            for row in results[1:]:
                csv_writer.writerow(row)
                data_rows_written += 1
            
            # Write EEPROM calibration data section
            if frequency_data and gain_data:
                csv_writer.writerow(["#"])
                csv_writer.writerow(["# EEPROM Calibration Data"])
                csv_writer.writerow(["# eeprom_frequency_hz", "eeprom_gain_db"])
                for freq, gain in zip(frequency_data, gain_data):
                    csv_writer.writerow([freq, gain])
        
        print(f"✓ CSV file saved: {csv_filename}")
        print(f"  Path: {csv_full_path}")
        print(f"  Header written with metadata")
        print(f"  Data rows written: {data_rows_written}")
        
        # Generate plots automatically after saving CSV file
        if plot_results:
            print("\n--- Generating Plots ---")
            plot_noise_density(csv_full_path)
        
    except Exception as e:
        print(f"✗ Failed to save CSV file: {e}")
        import traceback
        traceback.print_exc()
    

    # Display results to console
    if display_results:         
        print("\n--- Noise Density Measurement Results ---")
        for row in results:
            print("\t".join(str(cell) for cell in row))
        print("--- End of Results ---")

    # Generate data summary
    if display_summary:
        if len(results) > 1:  # Skip header row
            print("\n--- Data Summary ---")
            
            # Extract frequency and noise density data (skip header row)
            frequencies = [float(row[0]) for row in results[1:]]
            measured_noise_densities = [float(row[1]) for row in results[1:]]
            
            # Check if we have LNA input noise data (4th column)
            lna_input_noise_densities = []
            has_gain_data = False
            try:
                lna_input_noise_densities = [float(row[3]) if row[3] is not None else None for row in results[1:]]
                has_gain_data = any(val is not None for val in lna_input_noise_densities)
            except (IndexError, ValueError):
                has_gain_data = False
            
            # Basic statistics for measured noise
            min_freq = min(frequencies)
            max_freq = max(frequencies)
            min_measured_noise = min(measured_noise_densities)
            max_measured_noise = max(measured_noise_densities)
            avg_measured_noise = sum(measured_noise_densities) / len(measured_noise_densities)
            
            # Find frequencies where min/max noise occur
            min_measured_noise_freq = frequencies[measured_noise_densities.index(min_measured_noise)]
            max_measured_noise_freq = frequencies[measured_noise_densities.index(max_measured_noise)]
            
            # Statistics for LNA input noise if available
            if has_gain_data:
                valid_lna_noise = [val for val in lna_input_noise_densities if val is not None]
                if valid_lna_noise:
                    min_lna_noise = min(valid_lna_noise)
                    max_lna_noise = max(valid_lna_noise)
                    avg_lna_noise = sum(valid_lna_noise) / len(valid_lna_noise)
                    
                    # Find corresponding frequencies
                    min_lna_idx = lna_input_noise_densities.index(min_lna_noise)
                    max_lna_idx = lna_input_noise_densities.index(max_lna_noise)
                    min_lna_noise_freq = frequencies[min_lna_idx]
                    max_lna_noise_freq = frequencies[max_lna_idx]
            
            print(f"Measurement Parameters:")
            print(f"  Sample Frequency: {sample_frequency/1e6:.1f} MHz")
            print(f"  FFT Averages: {fft_average_count}")
            print(f"  Sample Size: {sample_size:,} points")
            print(f"  FFT Bin Size: {analyzer.fft_bin_size:.2f} Hz")
            
            print(f"\nFrequency Range:")
            print(f"  Start: {min_freq:.1f} Hz")
            print(f"  End: {max_freq/1e6:.3f} MHz")
            print(f"  Points: {len(frequencies)}")
            
            print(f"\nMeasured Noise Density Statistics:")
            print(f"  Minimum: {min_measured_noise:.2e} V/√Hz at {min_measured_noise_freq/1e3:.1f} kHz")
            print(f"  Maximum: {max_measured_noise:.2e} V/√Hz at {max_measured_noise_freq/1e3:.1f} kHz")
            print(f"  Average: {avg_measured_noise:.2e} V/√Hz")
            print(f"  Dynamic Range: {max_measured_noise/min_measured_noise:.1f}x ({20*abs(math.log10(max_measured_noise/min_measured_noise)):.1f} dB)")
            
            # Display LNA input noise statistics if available
            if has_gain_data and valid_lna_noise:
                print(f"\nLNA Input Noise Density Statistics (Gain Compensated):")
                print(f"  Minimum: {min_lna_noise:.2e} V/√Hz at {min_lna_noise_freq/1e3:.1f} kHz")
                print(f"  Maximum: {max_lna_noise:.2e} V/√Hz at {max_lna_noise_freq/1e3:.1f} kHz") 
                print(f"  Average: {avg_lna_noise:.2e} V/√Hz")
                print(f"  Dynamic Range: {max_lna_noise/min_lna_noise:.1f}x ({20*abs(math.log10(max_lna_noise/min_lna_noise)):.1f} dB)")
            
            # Calculate RMS noise over different frequency bands
            
            # Low frequency band (< 1 kHz)
            low_freq_data = [(f, n) for f, n in zip(frequencies, measured_noise_densities) if f < 1000]
            if low_freq_data:
                low_freq_avg = sum(n for f, n in low_freq_data) / len(low_freq_data)
                print(f"\nFrequency Band Analysis (Measured Noise):")
                print(f"  Low Freq (<1 kHz): {low_freq_avg:.2e} V/√Hz (avg, {len(low_freq_data)} points)")
            
            # Mid frequency band (1 kHz - 100 kHz)
            mid_freq_data = [(f, n) for f, n in zip(frequencies, measured_noise_densities) if 1000 <= f < 100000]
            if mid_freq_data:
                mid_freq_avg = sum(n for f, n in mid_freq_data) / len(mid_freq_data)
                print(f"  Mid Freq (1-100 kHz): {mid_freq_avg:.2e} V/√Hz (avg, {len(mid_freq_data)} points)")
            
            # High frequency band (>= 100 kHz)
            high_freq_data = [(f, n) for f, n in zip(frequencies, measured_noise_densities) if f >= 100000]
            if high_freq_data:
                high_freq_avg = sum(n for f, n in high_freq_data) / len(high_freq_data)
                print(f"  High Freq (≥100 kHz): {high_freq_avg:.2e} V/√Hz (avg, {len(high_freq_data)} points)")
        
        else:
            print("\n✗ No data available for summary")

    #disconnect from the devices
    analyzer.reset_averages()
    analyzer.disconnect()       
    print("Disconnected from LTpowerAnalyzer")
    
    lna_device.close()
    print("Disconnected from LNAmplifier")

except Exception as e:
    print(f"Error during test: {e}")
    # Ensure cleanup on error
    try:
        if 'analyzer' in locals():
            analyzer.disconnect()
    except:
        pass
    try:
        if 'lna_device' in locals():
            lna_device.close()
    except:
        pass 