#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LTPowerAnalyzer Input Noise Density Measurement

This script measures the input noise density of the LTPowerAnalyzer without any
device under test connected. It characterizes the analyzer's inherent input noise
floor using FFT analysis across a specified frequency range.

Features:
- Configurable frequency range and measurement parameters
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
    python LTPowerAnalyzerNoiseDensity.py

Requirements:
    - LTpowerAnalyzer device connected via USB
    - No device under test (measures analyzer's inherent noise)

History:
    10-21-2025  v1.0.0 - Initial LTPowerAnalyzer noise density measurement script
"""

# Import libraries
import sys
import os
import time
import msvcrt
import math
import csv
from datetime import datetime

# Add the root project directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from Drivers.LTpowerAnalyzerDriver import LTpowerAnalyzer

try:
    debug = False

    #setup the measurement parameters
    sample_frequency = 5e6
    fft_average_count = 16
    point_count = 401
    sample_size = 2**22
    start_frequency = 10.0
    end_frequency = 1.0e6

    # Connect to LTpowerAnalyzer
    analyzer = LTpowerAnalyzer(debug)
    print("Connecting to LTpowerAnalyzer...")
    if not analyzer.connect():
        print("Failed to connect to LTpowerAnalyzer")
        exit()
    
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
    results.append(["FFT Frequency (Hz)", "Input Noise Density (V/√Hz)"])
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
            frequency_data = analyzer.fft_frequency[fft_bin]
            noise_data = analyzer.fft_input_noise_density[fft_bin]
            results.append([frequency_data, noise_data])
            used_bins.add(fft_bin)
            
            if len(results) <= 6:  # Show first 5 data points for debugging (including header)
                print(f"  Point {len(results)-1}: {frequency_data:.2f} Hz, {noise_data:.2e} V/√Hz")
    
    print(f"✓ Collected {len(results)-1} unique data points (excluding header)")
    
    # Debug: Check if we have data
    if len(results) <= 1:
        print("⚠ Warning: No data collected! Check measurement execution.")
    else:
        print(f"✓ Data collection successful: {len(results)-1} points")
    
    # Save results to CSV file
    print("\n--- Saving Data to CSV File ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_filename = f"ltpoweranalyzer_noise_density_{timestamp}.csv"
    csv_full_path = os.path.join(script_dir, csv_filename)
    
    try:
        with open(csv_full_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header with metadata
            csv_writer.writerow(["# LTPowerAnalyzer Input Noise Density Measurement"])
            csv_writer.writerow([f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            csv_writer.writerow([f"# Sample Frequency: {sample_frequency/1e6:.1f} MHz"])
            csv_writer.writerow([f"# FFT Averages: {fft_average_count}"])
            csv_writer.writerow([f"# Sample Size: {sample_size} points"])
            csv_writer.writerow([f"# FFT Bin Size: {analyzer.fft_bin_size:.2f} Hz"])
            csv_writer.writerow([f"# Total Test Frequencies: {len(test_frequencies)}"])
            csv_writer.writerow([f"# Unique Data Points: {len(results)-1}"])
            csv_writer.writerow(["#"])
            
            # Write column headers
            csv_writer.writerow(["frequency", "input_noise_density"])
            
            # Write data rows (skip the original header row from results)
            data_rows_written = 0
            for row in results[1:]:
                csv_writer.writerow(row)
                data_rows_written += 1
        
        print(f"✓ CSV file saved: {csv_filename}")
        print(f"  Path: {csv_full_path}")
        print(f"  Header written with metadata")
        print(f"  Data rows written: {data_rows_written}")
        
    except Exception as e:
        print(f"✗ Failed to save CSV file: {e}")
        import traceback
        traceback.print_exc()
    

    # Display results to console
    print("\n--- Noise Density Measurement Results ---")
    for row in results:
        print("\t".join(str(cell) for cell in row))
    print("--- End of Results ---")

    # Generate data summary
    if len(results) > 1:  # Skip header row
        print("\n--- Data Summary ---")
        
        # Extract frequency and noise density data (skip header row)
        frequencies = [float(row[0]) for row in results[1:]]
        noise_densities = [float(row[1]) for row in results[1:]]
        
        # Basic statistics
        min_freq = min(frequencies)
        max_freq = max(frequencies)
        min_noise = min(noise_densities)
        max_noise = max(noise_densities)
        avg_noise = sum(noise_densities) / len(noise_densities)
        
        # Find frequencies where min/max noise occur
        min_noise_freq = frequencies[noise_densities.index(min_noise)]
        max_noise_freq = frequencies[noise_densities.index(max_noise)]
        
        print(f"Measurement Parameters:")
        print(f"  Sample Frequency: {sample_frequency/1e6:.1f} MHz")
        print(f"  FFT Averages: {fft_average_count}")
        print(f"  Sample Size: {sample_size:,} points")
        print(f"  FFT Bin Size: {analyzer.fft_bin_size:.2f} Hz")
        
        print(f"\nFrequency Range:")
        print(f"  Start: {min_freq:.1f} Hz")
        print(f"  End: {max_freq/1e6:.3f} MHz")
        print(f"  Points: {len(frequencies)}")
        
        print(f"\nNoise Density Statistics:")
        print(f"  Minimum: {min_noise:.2e} V/√Hz at {min_noise_freq/1e3:.1f} kHz")
        print(f"  Maximum: {max_noise:.2e} V/√Hz at {max_noise_freq/1e3:.1f} kHz")
        print(f"  Average: {avg_noise:.2e} V/√Hz")
        print(f"  Dynamic Range: {max_noise/min_noise:.1f}x ({20*abs(math.log10(max_noise/min_noise)):.1f} dB)")
        
        # Calculate RMS noise over different frequency bands
        
        # Low frequency band (< 1 kHz)
        low_freq_data = [(f, n) for f, n in zip(frequencies, noise_densities) if f < 1000]
        if low_freq_data:
            low_freq_avg = sum(n for f, n in low_freq_data) / len(low_freq_data)
            print(f"\nFrequency Band Analysis:")
            print(f"  Low Freq (<1 kHz): {low_freq_avg:.2e} V/√Hz (avg, {len(low_freq_data)} points)")
        
        # Mid frequency band (1 kHz - 100 kHz)
        mid_freq_data = [(f, n) for f, n in zip(frequencies, noise_densities) if 1000 <= f < 100000]
        if mid_freq_data:
            mid_freq_avg = sum(n for f, n in mid_freq_data) / len(mid_freq_data)
            print(f"  Mid Freq (1-100 kHz): {mid_freq_avg:.2e} V/√Hz (avg, {len(mid_freq_data)} points)")
        
        # High frequency band (>= 100 kHz)
        high_freq_data = [(f, n) for f, n in zip(frequencies, noise_densities) if f >= 100000]
        if high_freq_data:
            high_freq_avg = sum(n for f, n in high_freq_data) / len(high_freq_data)
            print(f"  High Freq (≥100 kHz): {high_freq_avg:.2e} V/√Hz (avg, {len(high_freq_data)} points)")
    
    else:
        print("\n✗ No data available for summary")

    #disconnect from the analyzer 
    analyzer.reset_averages()
    analyzer.disconnect()       
    print("Disconnected from LTpowerAnalyzer")

except Exception as e:
    print(f"Error during test: {e}")
    # Ensure cleanup on error
    try:
        if 'analyzer' in locals():
            analyzer.disconnect()
    except:
        pass 