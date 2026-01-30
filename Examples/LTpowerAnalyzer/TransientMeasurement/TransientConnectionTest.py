#!/usr/bin/env python3
"""
LTpowerAnalyzer Transient Connection Test

This script tests the basic transient measurement functionality
and verifies the connection to the LTpowerAnalyzer hardware.

Requirements:
- LTpowerAnalyzer hardware connected
- LTpowerAnalyzer software installed
- Current probe connected

Author: Analog Devices, Inc.
License: See LICENSE.txt
"""

import sys
import os

# Add the Drivers directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
drivers_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'Drivers')
sys.path.append(drivers_dir)

from LTpowerAnalyzerDriver import LTpowerAnalyzer

def main():
    """Main function for testing transient measurement connection"""
    
    print("=" * 60)
    print("LTpowerAnalyzer Transient Measurement Connection Test")
    print("=" * 60)
    
    # Initialize the LTpowerAnalyzer with debug enabled
    analyzer = LTpowerAnalyzer(debug=True)
    
    # Test 1: Basic connection
    print("\n1. Testing basic connection...")
    if not analyzer.connect():
        print("❌ Failed to connect to LTpowerAnalyzer")
        print("Please check:")
        print("  - Hardware is connected via USB")
        print("  - LTpowerAnalyzer software is installed")
        print("  - No other applications are using the device")
        return False
    
    print("✅ Successfully connected to LTpowerAnalyzer")
    
    # Test 2: Check current probe connection and capabilities
    print("\\n2. Testing current probe connection and capabilities...")
    try:
        if analyzer.current_probe_connected:
            probe_info = analyzer.get_current_probe_info()
            print(f"✅ Current probe connected: {probe_info['name']}")
            print(f"  Probe Type: {probe_info['type']}")
            print(f"  Max Current: {probe_info['max_current']:.1f} A")
            print(f"  Max DC Current: {probe_info['max_dc_current']:.1f} A")
            print(f"  Temperature: {probe_info['temperature']:.1f}°C")
            print(f"  Error Status: {'Error' if probe_info['error'] else 'OK'}")
            
            if probe_info['error']:
                print("⚠️  Warning: Probe has an error condition")
            
        else:
            print("❌ Current probe is not connected")
            print("Please connect a current probe to test transient measurements")
            analyzer.disconnect()
            return False
    except Exception as e:
        print(f"❌ Error checking current probe: {e}")
        analyzer.disconnect()
        return False
    
    # Test 3: Initialize transient measurement
    print("\n2. Testing transient measurement initialization...")
    try:
        if analyzer.initialize_transient_measurement():
            print("✅ Transient measurement initialized successfully")
        else:
            print("❌ Failed to initialize transient measurement")
            analyzer.disconnect()
            return False
    except Exception as e:
        print(f"❌ Error initializing transient measurement: {e}")
        analyzer.disconnect()
        return False
    
    # Test 3: Create configuration objects
    print("\n3. Testing configuration object creation...")
    try:
        # Test transient configuration
        transient_config = LTpowerAnalyzer.TransientSetup(
            current1=0.0,
            current2=0.1,
            pulse_width=1e-3,
            pulse_count=1,
            duty_cycle=0.5,
            rise_time=1e-6,
            fall_time=1e-6,
            acquisition_time=5e-3,
            measure_switching_frequency=False
        )
        print("✅ TransientSetup configuration created")
        
        # Test trigger configuration  
        trigger_config = LTpowerAnalyzer.TriggerSetup(
            channel=1,                 # Trigger on current
            level=safe_current / 2.0,  # Half of max current
            delay=0.0,
            timeout=1.0,
            slope=0,                   # Rising edge
            auto=True
        )
        print("✅ TriggerSetup configuration created")
        
        # Test PWL points
        pwl_points = [
            LTpowerAnalyzer.PWLPoint(0.0, 0.0),
            LTpowerAnalyzer.PWLPoint(1e-3, 0.1),
            LTpowerAnalyzer.PWLPoint(2e-3, 0.0)
        ]
        print("✅ PWL points created")
        
    except Exception as e:
        print(f"❌ Error creating configuration objects: {e}")
        analyzer.disconnect()
        return False
    
    # Test 4: Test utility functions
    print("\\n5. Testing PWL utility functions...")
    try:
        # Test step creation
        step_points = analyzer.create_pwl_step(0.0, 0.2, 1e-3, 2e-3, 5e-3)
        print(f"✅ PWL step created with {len(step_points)} points")
        
        # Test ramp creation
        ramp_points = analyzer.create_pwl_ramp(0.0, 0.3, 3e-3)
        print(f"✅ PWL ramp created with {len(ramp_points)} points")
        
        # Test pulse train creation
        pulse_points = analyzer.create_pwl_pulse_train(0.1, 0.4, 0.5e-3, 2e-3, 2)
        print(f"✅ PWL pulse train created with {len(pulse_points)} points")
        
    except Exception as e:
        print(f"❌ Error testing utility functions: {e}")
        analyzer.disconnect()
        return False
    
    # Test 6: Test property access (read-only, so safe to test)
    print("\\n6. Testing transient data property access...")
    try:
        # These should return None or default values when no measurement has been made
        input_data = analyzer.transient_input_data
        output_data = analyzer.transient_output_data
        sample_freq = analyzer.transient_sample_frequency
        sample_count = analyzer.transient_sample_count
        time_array = analyzer.get_transient_time_array()
        
        print("✅ Transient data properties accessible")
        print(f"  Sample frequency: {sample_freq} Hz")
        print(f"  Sample count: {sample_count}")
        print(f"  Time array length: {len(time_array)}")
        
    except Exception as e:
        print(f"❌ Error accessing transient data properties: {e}")
        analyzer.disconnect()
        return False
    
    # Clean up
    print("\\n7. Disconnecting...")
    analyzer.disconnect()
    print("✅ Disconnected successfully")
    
    print("\n" + "=" * 60)
    print("✅ ALL TRANSIENT MEASUREMENT TESTS PASSED!")
    print("✅ Transient measurement functionality is ready to use")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Some tests failed. Please check the hardware connection and try again.")
        sys.exit(1)