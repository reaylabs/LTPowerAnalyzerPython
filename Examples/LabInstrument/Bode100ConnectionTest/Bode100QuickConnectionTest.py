#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bode100 Quick Connection Example

This script demonstrates a simple direct connection to a Bode100 network analyzer
using TCPIP/SOCKET connection. It connects to the instrument, queries the 
identification string, and disconnects.

Usage:
    python Bode100QuickConnection.py

Requirements:
    - Bode100 network analyzer with SCPI server enabled
    - Network connection to the instrument
    - pyvisa package: pip install pyvisa
    - VISA drivers installed

Configuration:
    Update SCPI_server_IP and SCPI_Port variables to match your instrument settings.

History:
    10-17-2025  v1.0.0 - Initial quick connection example
"""

# use pyvisa or similar package
import pyvisa 

# IMPORTANT SETUP INSTRUCTIONS:
# For this script to work, you must first configure the Bode100 SCPI server:
# 1. Open the Bode100 Analyzer GUI software
# 2. Click on the "Advanced" tab
# 3. Find and select the "SCPI Server" option
# 4. Start the SCPI server
# 5. The IP address and Port numbers will be displayed in the GUI
# 6. Update the variables below with the displayed IP and Port values

# *** TO DO: adapt IP address and SCPI port according to your instrument ***
SCPI_server_IP = '192.168.4.90'  # Replace with IP shown in Bode100 GUI
SCPI_Port = '5025'               # Replace with Port shown in Bode100 GUI

VISA_resource_name = 'TCPIP::' + SCPI_server_IP + '::' + SCPI_Port + '::SOCKET'

print('Trying to connect to VISA resource: ' + VISA_resource_name)
visaSession = pyvisa.ResourceManager().open_resource(VISA_resource_name)
visaSession.read_termination = '\n'

print('SCPI client connected to SCPI server: ' + visaSession.query("*IDN?"))
visaSession.close()