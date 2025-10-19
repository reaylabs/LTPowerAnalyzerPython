"""
LTPowerAnalyzer Python - Utility Functions
============================================

This module provides common utility functions for electrical engineering calculations
and data formatting used throughout the LTPowerAnalyzer Python project.

Functions:
    calculate_series_RC(): Calculate series R and C from impedance measurements
    calculate_fc_from_rc(): Calculate cutoff frequency for RC filters  
    to_engineering(): Format numbers in engineering notation with SI prefixes

Author: Analog Devices, Inc.
Date: October 2025
License: See LICENSE.txt in project root
"""

import csv
import math

def calculate_series_RC(magnitude, phase, frequency):
    """
    Calculate series resistance (R) and capacitance (C) from impedance measurements.
    
    This function extracts the equivalent series resistance and capacitance from
    impedance magnitude and phase measurements at a given frequency. It assumes
    a series RC circuit model where:
    
    Z = R + jX_C = R - j/(2πfC)
    
    The impedance magnitude and phase are related by:
    |Z| = √(R² + X_C²)
    θ = arctan(X_C/R) = arctan(-1/(2πfRC))
    
    Args:
        magnitude (float): Impedance magnitude |Z| in ohms (Ω)
        phase (float): Phase angle in degrees (°). Negative for capacitive loads
        frequency (float): Test frequency in hertz (Hz)
    
    Returns:
        tuple: (R, C) where:
            R (float): Series resistance in ohms (Ω)
            C (float): Series capacitance in farads (F)
    
    Raises:
        ValueError: If frequency is <= 0 or if X_C is zero (purely resistive)
        
    Example:
        >>> # Measure impedance at 1 kHz: |Z| = 100Ω, θ = -45°
        >>> R, C = calculate_series_RC(100, -45, 1000)
        >>> print(f"R = {R:.1f} Ω, C = {to_engineering(C, 'F')}")
        R = 70.7 Ω, C = 2.25 µF
        
    Note:
        This function assumes a series RC model. For parallel RC circuits or
        other circuit topologies, different analysis methods are required.
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

def calculate_fc_from_rc(R, C):
    """
    Calculate the cutoff frequency for an RC low-pass filter.
    
    The cutoff frequency (also known as corner frequency or -3dB frequency)
    is the frequency at which the output voltage is reduced to 70.7% of the
    input voltage (or -3dB).
    
    Formula: fc = 1 / (2π × R × C)
    
    Args:
        R (float): Resistance in ohms (Ω)
        C (float): Capacitance in farads (F)
    
    Returns:
        float: Cutoff frequency in hertz (Hz)
        
    Example:
        >>> fc = calculate_fcfrom_rc(1000, 1e-6)  # 1kΩ, 1µF
        >>> print(f"Cutoff frequency: {fc:.2f} Hz")
        Cutoff frequency: 159.15 Hz
    """
    return 1.0 / (2.0 * math.pi * R * C)

def to_engineering(value, unit=''):
    """
    Format a numerical value using engineering notation with SI prefixes.
    
    Engineering notation expresses numbers as a coefficient (1-999) multiplied
    by a power of 1000, using standard SI prefixes (k, M, G, etc.).
    
    Args:
        value (float): The numerical value to format
        unit (str, optional): The unit string to append (e.g., 'Hz', 'V', 'Ω')
    
    Returns:
        str: Formatted string with SI prefix and unit
        
    Supported Prefixes:
        p (pico, 10^-12)
        n (nano, 10^-9)  
        µ (micro, 10^-6)
        m (milli, 10^-3)
        (none, 10^0)
        k (kilo, 10^3)
        M (mega, 10^6)
        G (giga, 10^9)
        
    Example:
        >>> print(to_engineering(1500, 'Hz'))
        1.5 kHz
        >>> print(to_engineering(0.000047, 'F'))
        47 µF
        >>> print(to_engineering(2200000, 'Ω'))
        2.2 MΩ
    """
    # SI prefix mapping: [p, n, µ, m, (none), k, M, G]
    prefixes = ['p', 'n', 'µ', 'm', '', 'k', 'M', 'G']
    
    # Handle zero case
    if value == 0:
        return f"0 {unit}"
    
    # Calculate the power of 1000 (engineering exponent)
    exp = int(math.floor(math.log10(abs(value)) / 3))
    
    # Limit to available prefixes (pico to giga)
    exp3 = max(min(exp, 4), -4)
    
    # Scale the value
    scaled = value / (10 ** (3 * exp3))
    
    # Format with appropriate prefix
    return f"{scaled:.4g} {prefixes[exp3 + 4]}{unit}"

def save_data_to_csv(headers, data_rows, full_path):
    """Save measurement data to CSV file"""
    try:
        with open(full_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header using the actual headers from the measurement
            writer.writerow(headers)
            # Write data
            for row in data_rows:
                writer.writerow(row)
        print(f"✓ Data saved to: {full_path}")
    except Exception as e:
        print(f"⚠ Warning: Could not save data to CSV: {e}")