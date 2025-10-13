#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LTpowerAnalyzer Connection Test Example

This script demonstrates how to connect to an LTpowerAnalyzer device using the 
LTpowerAnalyzer class. It performs a basic connection test, displays device 
information, and properly disconnects from the device.

Usage:
    python ConnectionTest.py

Requirements:
    - pythonnet package (install with: pip install pythonnet)
    - LTpowerAnalyzer hardware connected to the system
"""

import sys
import os

# Add the root project directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.append(project_root)

from Drivers.LTpowerAnalyzerDriver import LTpowerAnalyzer

# Main execution block with error handling
try:
    # Create analyzer instance with debug output enabled
    debug = True
    analyzer = LTpowerAnalyzer(debug)
    
    # Attempt to connect to the device
    print("Connecting to LTpowerAnalyzer...")
    if not analyzer.connect():
        print("Failed to connect to LTpowerAnalyzer")
        exit()
    
    # Connection successful - display device information
    print("Connected to LTpowerAnalyzer")
    analyzer.display_meter_info()
    
    # Clean up - disconnect from the device
    analyzer.disconnect()
    print("Connection test completed successfully")
    
except Exception as e:
    # Handle any errors that occur during execution
    print(f"Error during usage of LTpowerAnalyzer: {e}")