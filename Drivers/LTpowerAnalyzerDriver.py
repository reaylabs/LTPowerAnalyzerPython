# -*- coding: utf-8 -*-
r"""
LTpowerAnalyzer Python Driver

A Python wrapper for the LTpowerAnalyzer .NET driver, providing easy access to 
power measurement and analysis functionality.

Features:
    - Device connection and configuration management
    - Real-time power measurement and data acquisition
    - FFT analysis with configurable parameters
    - Trigger setup and sampling configuration
    - Comprehensive error handling and debugging support

Requirements:
    - Python 3.7+
    - pythonnet package: pip install pythonnet
    - LTpowerAnalyzer software installed (C:\Program Files (x86)\LTpowerAnalyzer)
    - LTpowerAnalyzer hardware device

Dependencies (automatically loaded from LTpowerAnalyzer install directory):
    - LTpowerAnalyzerDriver.dll (main .NET assembly)
    - libm2k-sharp.dll (.NET bindings)
    - libm2k-sharp-cxx-wrap.dll (native C++ wrapper)

Author: Analog Devices, Inc.
License: See LICENSE.txt
"""

import numpy as np
import clr
import os
from dataclasses import dataclass

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the LTPowerAnalyzer install directory
ltpoweranalyzer_install_dir = r"C:\Program Files (x86)\LTpowerAnalyzer"

# Add the install directory to the system PATH so native DLLs can be found
import sys
if ltpoweranalyzer_install_dir not in os.environ.get('PATH', ''):
    os.environ['PATH'] = ltpoweranalyzer_install_dir + os.pathsep + os.environ.get('PATH', '')

# Add the CLR system reference
clr.AddReference("System")
from System.Reflection import Assembly

# Load required .NET dependencies from install directory
libm2k_sharp_path = os.path.join(ltpoweranalyzer_install_dir, "libm2k-sharp.dll")

try:
    # Only load .NET assemblies with clr.AddReference
    # libm2k-sharp.dll is a .NET assembly
    clr.AddReference(libm2k_sharp_path)
except Exception as e:
    print(f"Warning: Could not load libm2k-sharp dependency: {e}")

# Note: libm2k-sharp-cxx-wrap.dll is a native C++ DLL and will be loaded 
# automatically by the system when needed by the .NET assemblies

# Load the main assembly from the install directory
assembly_path = os.path.join(ltpoweranalyzer_install_dir, "LTpowerAnalyzerDriver.dll")
clr.AddReference(assembly_path) 
from LTpowerAnalyzerDriver import LTpowerAnalyzer as LTpowerAnalyzerDriver

class LTpowerAnalyzer:
    
    @dataclass
    class TriggerSetup:
        """Configuration class for trigger parameters"""
        channel: int = 0           # 0 = Channel 1, 1 = Channel 2
        level: float = 0.0         # voltage offset
        delay: float = 0.0         # time offset
        timeout: float = 0.1       # Amount of time to wait for trigger before auto-triggering
        slope: int = 0             # 0 = rising, 1 = falling
        auto: bool = True          # Enable auto-triggering
    
    @dataclass
    class SampleSetup:
        """Configuration class for sampling parameters"""
        sample_size: int = 16384           # Sample size (must be a power of 2)
        frequency: float = 1.25e6   # Sample frequency in hertz
        fft_average_count: int = 1      # Fft average count (must be a power of 2)
        gain_average_count: int = 1      # Fft gain average count (must be a power of 2)
        filter_frequency: float = 10000  # Cutoff frequency in hertz
        filter_enable: bool = False # Enable/disable lowpass filter


    def __init__(self, debug=False):
        """Constructor for the LTpowerAnalyzer class"""
        try:
            self.meter = LTpowerAnalyzerDriver()
            self.isConnected = False
            self.debug = debug  # Debug flag for status messages
        except Exception as e:
            print(f"Error initializing LTpowerAnalyzer: {e}")

    #add a property for the bin size
    @property
    def fft_bin_size(self):
        """Read-only property that returns the current bin size in Hz"""
        return self.meter.AcFFTBinSize
    
    @property
    def fft_average_count(self):
        """Read-only property that returns the current fft average count"""
        return self.meter.AcFFTAverageCount
    
    @property
    def fft_effective_noise_bandwidth(self):
        """Read-only property that returns the current fft effective noise bandwidth in Hz"""
        return self.meter.AcFFTEffectiveNoiseBandwidth
    
    @property
    def fft_frequency(self):
        """Read-only property that returns the current fft frequency data"""
        return self.meter.AcFFTFrequencyData
    
    @property
    def fft_gain_magnitude(self):
        """Read-only property that returns the current fft gain data"""
        return self.meter.AcFFTGainData
    
    @property
    def fft_input(self):
        """Read-only property that returns the current fft input data"""
        return self.meter.AcFFTInputData
    
    @property
    def fft_input_noise_density(self):
        """Read-only property that returns the current fft input noise density"""
        return self.meter.AcFFTInputNoiseDensity
    
    @property
    def fft_output(self):
        """Read-only property that returns the current fft output data"""
        return self.meter.AcFFTOutputData
    
    @property
    def fft_output_noise_density(self):
        """Read-only property that returns the current fft output noise density"""
        return self.meter.AcFFTOutputNoiseDensity
    
    @property
    def fft_gain_phase(self):
        """Read-only property that returns the current fft phase data"""
        return self.meter.AcFFTPhaseData

    @property
    def fft_window(self):
        """Read-only property that returns the current fft phase data"""
        return self.meter.AcFFTWindow     
    
    #gain average count
    @property
    def gain_average_count(self):
        """Read-only property that returns the current gain average count"""
        return self.meter.AcGainAverageCount
    
    @property
    def is_connected(self):
        """Read-only property that returns the connection status"""
        return self.isConnected

    @property
    def injection_frequency(self):
        """Read-only property that returns the current injection frequency in Hz"""
        try:
            if self.isConnected:
                return self.meter.AcInjectionFrequency
            else:
                return 0.0
        except Exception as e:
            if self.debug:
                print(f"Error reading injection frequency: {e}")
            return 0.0

    @property
    def injection_amplitude(self):
        """Read-only property that returns the current injection amplitude in Volts"""
        try:
            if self.isConnected:
                return self.meter.AcInjectionAmplitude
            else:
                return 0.0
        except Exception as e:
            if self.debug:
                print(f"Error reading injection amplitude: {e}")
            return 0.0

    #add property for the sample rate
    @property
    def sample_frequency(self):
        """Read-only property that returns the current sample rate in Hz"""
        return self.meter.AcSampleFrequency
    @property
    def sample_size(self):
        """Read-only property that returns the current sample size"""
        return self.meter.AcFFTSampleSize

    @property
    def sample_size_max(self):
        """Read-only property that returns the maximum sample size"""
        return self.meter.AcMaxInputSampleSize

    def _check_connection(self):
        """Run the CheckConnection to determine if the meter is connected"""
        try:
            self.meter.CheckConnections()
            if self.meter.AcMeterConnected:
                self.isConnected = True
            else:
                self.isConnected = False
        except Exception as e:
            print(f"Error checking connections: {e}")
            self.isConnected = False

    def connect(self):
        """Connect to the LTpowerAnalyzer """
        try:
            self._check_connection()
            if self.isConnected:
                self.display_meter_info()
            return self.isConnected
        except Exception as e:
            print(f"Error initializing meter: {e}")
            return False

    def disable_injection_output(self):
        """Disable the injection signal output"""
        try:
            if not self.isConnected:
                print("Cannot disable injection output. Meter not connected.")
                return False
                
            if self.debug:
                print("Disabling injection output...")
            
            # Disable the injection signal output
            self.meter.AcDisableInjectionOutput()
            
            if self.debug:
                print("Injection output disabled successfully.")
            return True
            
        except Exception as e:
            print(f"Error disabling injection output: {e}")
            return False

    def display_meter_info(self):
        """ Display the LTpowerAnalyzer information """
        try:
            if self.isConnected:
                if self.debug:
                    print("Meter Connected")
                    print("Meter Name: ", self.meter.AcMeterName)
                if self.meter.AcCurrentProbeConnected:
                    if self.debug:
                        print("Current Probe Name: ", self.meter.AcCurrentProbeName)
                    self.meter.AcMeasureProbeVoltageAndTemperature()
                    if self.debug:
                        print("Probe Voltage: ", "{:.2f}".format(self.meter.AcOutputVoltage))
                        print("Probe Temperature: ", "{:.2f}".format(self.meter.AcCurrentProbeTemperature))
                else:
                    if self.debug:
                        print("Current Probe Not Connected")
            else:
                if self.debug:
                    print("Meter Not Connected")
        except Exception as e:
            print(f"Error displaying meter information: {e}")

    def disconnect(self):
        """ Disconnects the meter """
        try:
            if self.isConnected:
                self.meter.AcDisconnect()
                self.isConnected = False
                if self.debug:
                    print("Meter disconnected.")
            else:
                if self.debug:
                    print("Meter not connected.")
        except Exception as e:
            print(f"Error disconnecting meter: {e}")

    def execute_gain_phase_measurement(self):
        """Execute the gain-phase measurement"""
        if (self.debug):
            print(f"Executing gain-phase measurement")

        #The gain phase measurement will add the results to the running averages
        triggered = self.meter.AcExecuteGainPhaseMeasurement()
        if not triggered:
            print("Measurement not triggered")
    
    def get_closest_fft_frequency_and_bin(self, frequency: float):
        """Get the FFT bin and frequency from the frequency"""
        bin = int(round(frequency / self.meter.AcFFTBinSize))
        
        # Get the actual length of the FFT frequency array to ensure bounds checking
        max_bin = len(self.meter.AcFFTFrequencyData) - 1
        
        # Clamp the bin to valid range
        if bin < 0:
            bin = 0
        elif bin > max_bin:
            if (max_bin > 1):
                bin = max_bin
            
        center_frequency = bin * self.meter.AcFFTBinSize + self.meter.AcFFTBinSize / 2
        return center_frequency,bin
    
    def generate_test_frequencies(self, points_per_decade: int, low_decade: int, high_decade: int, include_last_point: bool = False):
        """Generate the test frequencies"""
        #generate the decade values
        interval = 10 / points_per_decade
        decade_values = []
        for i in range(points_per_decade):
            value = 1 + i * interval
            if (value < 10):
                decade_values.append(value)

        test_frequencies = []
        for decade in range(low_decade, high_decade):
            for decade_value in decade_values:
                test_frequencies.append(decade_value * (10 ** decade))
        
        #add the last decade value
        if (include_last_point):
            test_frequencies.append(10.0 ** (high_decade))

        return test_frequencies

    def bode100_log_points(self,f_start: float, f_end: float, num_points: int):
        """
        Generate logarithmically spaced frequency points.

        Always uses the exact step:
            step = (log10(f_end) - log10(f_start)) / (num_points - 1)

        Parameters:
            f_start (float): Start frequency (Hz)
            f_end   (float): End frequency (Hz)
            num_points (int): Number of points to generate

        Returns:
            numpy.ndarray: Array of frequencies (Hz)
        """
        f_start = float(f_start)
        f_end = float(f_end)
        if num_points < 2:
            raise ValueError("num_points must be >= 2")

        start_decade = np.log10(f_start)
        end_decade = np.log10(f_end)
        step = float((end_decade - start_decade) / (num_points - 1))
        n = np.arange(num_points)
        return f_start * (10 ** (step * n))
    
    def reset_averages(self):
            """Reset the averages"""
            self.meter.AcResetAverages()

    def set_fft_window(self, window_index: int):
        """Set the FFT window
        0 = Rectangular
        1 = Hamming
        2 = Hanning (default)
        3 = Blackman
        4 = Flat Top
        """
        if (window_index < 0 or window_index > 4):
            print(f"Invalid FFT window index: {window_index}")
            exit()
        window = self.fft_window
        window.value__ = window_index
        self.meter.AcFFTWindow = window

    def set_sample_frequency(self, frequency: float):
        """Set the sample frequency"""
        self.meter.AcSetSampleFrequency(frequency)

    def set_sample_size(self, size: int):
        """Set the sample size"""
        if (size > self.sample_size_max):
            print(f"Sample size {size} is greater than the maximum sample size 262144")
            exit()
        self.meter.AcSetSampleSize(size)
        
    def setup_gain_phase_measurement(self, sample_config: 'LTpowerAnalyzer.SampleSetup', injection_amplitude: float = 0.0):
        """Configure the gain-phase measurement parameters using a SampleSetup configuration object"""
        try:
            if not self.isConnected:
                print("Cannot setup gain-phase measurement. Meter not connected.")
                return False
                
            if self.debug:
                print("Setting up gain-phase measurement with provided configuration...")
                print(f"  Sample Size: {sample_config.sample_size}")
                print(f"  Sample Frequency: {sample_config.frequency} Hz")
                print(f"  FFT Average Count: {sample_config.fft_average_count}")
                print(f"  Gain Average Count: {sample_config.gain_average_count}")
                print(f"  Filter Enable: {sample_config.filter_enable}")
                if sample_config.filter_enable:
                    print(f"  Filter Frequency: {sample_config.filter_frequency} Hz")
                print(f"  Injection Amplitude: {injection_amplitude} V")
            
            # Initialize the scope for gain-phase measurement
            self.meter.AcInitializeScopeGainPhaseMeasurement()
            
            # Set FFT parameters
            self.meter.AcSetFFTAverageCount(sample_config.fft_average_count)
            self.meter.AcSetGainAverageCount(1)
            
            # Configure lowpass filter
            if sample_config.filter_enable:
                self.meter.AcEnableLowpassFilter(sample_config.filter_frequency)
            else:
                self.meter.AcDisableLowPassFilter()
            
            # Set sampling parameters
            self.meter.AcSetSampleFrequency(sample_config.frequency)
            self.meter.AcSetSampleSize(sample_config.sample_size)
            
            self.meter.AcSetInjectionAmplitude(injection_amplitude)
            self.meter.AcResetAverages()
            
            if self.debug:
                print("Gain-phase measurement setup completed successfully.")
            return True
            
        except Exception as e:
            print(f"Error setting up gain-phase measurement: {e}")
            return False

    def setup_trigger(self, trigger_config: 'LTpowerAnalyzer.TriggerSetup'):
        """Configure the trigger settings using a TriggerSetup configuration object"""
        try:
            if not self.isConnected:
                print("Cannot setup trigger. Meter not connected.")
                return False
                
            if self.debug:
                print("Setting up trigger with provided configuration...")
                print(f"  Channel: {trigger_config.channel} ({'Output/Vout' if trigger_config.channel == 0 else 'Input/Current'})")
                print(f"  Level: {trigger_config.level} V")
                print(f"  Delay: {trigger_config.delay} s")
                print(f"  Timeout: {trigger_config.timeout} s")
                print(f"  Slope: {trigger_config.slope} ({'Rising' if trigger_config.slope == 0 else 'Falling' if trigger_config.slope == 1 else 'Either Edge'})")
                print(f"  Auto: {trigger_config.auto} ({'Auto mode' if trigger_config.auto else 'Normal mode'})")
            
            # Set the trigger using the TriggerSetup parameters
            self.meter.AcSetTrigger(
                trigger_config.channel,
                trigger_config.level,
                trigger_config.delay,
                trigger_config.timeout,
                trigger_config.slope,
                trigger_config.auto
            )
            
            if self.debug:
                print("Trigger setup completed successfully.")
            return True
            
        except Exception as e:
            print(f"Error setting up trigger: {e}")
            return False

    def setup_injection(self, frequency: float, amplitude: float, transformer: bool = True):
        """Configure the injection signal frequency, amplitude, and output path"""
        try:
            if not self.isConnected:
                print("Cannot setup injection. Meter not connected.")
                return False
                
            if self.debug:
                print("Setting up injection signal")
                print(f"  Frequency: {frequency} Hz")
                print(f"  Amplitude: {amplitude} V")
                print(f"  Output: {transformer} ({'Transformer' if transformer else 'W1'})")
            
            # Set the injection amplitude based on the output path
            if transformer:
                # Use transformer output with frequency compensation
                self.meter.AcSetInjectionAmplitude(amplitude, True)
            else:
                # Use W1 output with frequency compensation
                self.meter.AcSetW1Amplitude(amplitude, True)  

            # Set the injection frequency
            self.meter.AcSetInjectionFrequency(frequency)
            return True
            
        except Exception as e:
            print(f"Error setting up injection: {e}")
            return False

    def start_injection_waveform(self):
        """Start the injection waveform"""
        try:
            if not self.isConnected:
                print("Cannot start injection waveform. Meter not connected.")
                return False
                
            if self.debug:
                print("Starting injection waveform...")
            
            # Start the injection waveform
            self.meter.AcStartInjectionWaveform()
            
            return True
            
        except Exception as e:
            print(f"Error starting injection waveform: {e}")
            return False

    def stop_injection_waveform(self):
        """Stop the injection waveform"""
        try:
            if not self.isConnected:
                print("Cannot stop injection waveform. Meter not connected.")
                return False
                
            if self.debug:
                print("Stopping injection waveform...")
            
            # Stop the injection waveform
            self.meter.AcStopInjectionWaveform()
            
            return True
            
        except Exception as e:
            print(f"Error stopping injection waveform: {e}")
            return False

   
 