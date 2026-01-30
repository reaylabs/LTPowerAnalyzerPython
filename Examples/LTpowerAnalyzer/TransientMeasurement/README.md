# LTpowerAnalyzer Transient Measurement

This directory contains examples and documentation for the transient measurement functionality in the LTpowerAnalyzer Python driver.

## Overview

The transient measurement capability allows you to perform time-domain analysis of power circuits under dynamic load conditions. This is particularly useful for:

- Load transient response testing
- Step load analysis
- Dynamic efficiency measurements
- Power supply stability analysis
- Custom load profile testing

## New Features Added

### Configuration Classes

- **`TransientSetup`**: Configuration for transient measurement parameters
- **`PWLPoint`**: Point definition for Piece-Wise Linear current profiles

### Core Functions

- **`initialize_transient_measurement()`**: Initialize the transient measurement system
- **`execute_transient_measurement()`**: Execute a standard step transient measurement
- **`execute_pwl_transient_measurement()`**: Execute a custom PWL transient measurement

### Current Probe Validation

- **`current_probe_connected`**: Check if current probe is connected
- **`current_probe_name`**: Get the name/model of the connected probe
- **`current_probe_max_current`**: Get maximum current capability of the probe
- **`current_probe_max_dc_current`**: Get maximum DC current based on voltage and probe type
- **`current_probe_temperature`**: Get current probe temperature
- **`current_probe_error`**: Check if probe has error conditions
- **`get_current_probe_info()`**: Get comprehensive probe information
- **`_validate_current_probe_capability()`**: Internal validation function

The driver automatically validates that:
- Current probe is connected before measurements
- Requested current levels are within probe capabilities  
- Probe is not in an error condition
- Probe temperature is within safe operating limits

Supported probe types: 1A, 10A, 50A, and 100A maximum current versions.

### Utility Functions

- **`create_pwl_step()`**: Create a current step profile
- **`create_pwl_ramp()`**: Create a current ramp profile  
- **`create_pwl_pulse_train()`**: Create a pulse train profile
- **`get_transient_time_array()`**: Generate corresponding time array for samples

### Data Properties

- **`transient_input_data`**: Current measurement data
- **`transient_output_data`**: Voltage measurement data
- **`transient_sample_frequency`**: Sample rate used for measurement
- **`transient_sample_count`**: Number of samples captured

## Files in this Directory

### TransientConnectionTest.py
A simple connection and functionality test script that verifies:
- Basic device connection
- Transient measurement initialization
- Configuration object creation
- Utility function operation
- Property access

Run this first to verify everything is working:
```bash
python TransientConnectionTest.py
```

### TransientMeasurementExample.py
A comprehensive example script demonstrating:
- Step transient measurements
- PWL (Piece-Wise Linear) transient measurements
- Pulse train measurements
- Data acquisition and analysis
- CSV data export
- Matplotlib plotting (optional)

Run this for full functionality demonstration:
```bash
python TransientMeasurementExample.py
```

## Usage Examples

### Basic Step Transient

```python
from LTpowerAnalyzerDriver import LTpowerAnalyzer

# Initialize and connect
analyzer = LTpowerAnalyzer(debug=True)
analyzer.connect()

# Check probe capabilities first
probe_info = analyzer.get_current_probe_info()
print(f"Connected probe: {probe_info['name']} ({probe_info['type']})")
print(f"Max current: {probe_info['max_current']} A")

# Initialize transient measurement
analyzer.initialize_transient_measurement()

# Configure step transient (automatically validates against probe limits)
transient_config = LTpowerAnalyzer.TransientSetup(
    current1=0.0,          # Low current: 0A
    current2=0.5,          # High current: 0.5A (will be validated against probe max)
    pulse_width=1e-3,      # Pulse width: 1ms
    pulse_count=1,         # Single pulse
    acquisition_time=10e-3 # Acquisition time: 10ms
)

# Configure trigger for current waveform
trigger_config = LTpowerAnalyzer.TriggerSetup(
    channel=1,             # Trigger on current (1) not voltage (0)
    level=0.25,            # Trigger level: half of max current (0.5A / 2)
    slope=0,               # Rising edge
    auto=True              # Auto trigger
)

# Execute measurement
success = analyzer.execute_transient_measurement(transient_config, trigger_config)

if success:
    # Get data
    input_data = analyzer.transient_input_data
    output_data = analyzer.transient_output_data
    time_array = analyzer.get_transient_time_array()
    
    # Process data...
```

### PWL Transient with Custom Profile

```python
# Create custom current profile
pwl_points = [
    LTpowerAnalyzer.PWLPoint(0.0e-3, 0.0),     # Start at 0A
    LTpowerAnalyzer.PWLPoint(1.0e-3, 0.5),     # Ramp to 0.5A at 1ms
    LTpowerAnalyzer.PWLPoint(5.0e-3, 0.5),     # Hold at 0.5A until 5ms
    LTpowerAnalyzer.PWLPoint(6.0e-3, 0.0)      # Return to 0A at 6ms
]

# Execute PWL measurement
success = analyzer.execute_pwl_transient_measurement(
    pwl_points,
    10e-3,              # 10ms acquisition time
    trigger_config
)
```

### Using Utility Functions

```python
# Create a pulse train
pulse_points = analyzer.create_pwl_pulse_train(
    current_low=0.1,       # 100mA baseline
    current_high=0.6,      # 600mA pulses
    pulse_width=1e-3,      # 1ms pulse width
    period=4e-3,           # 4ms period
    num_pulses=3           # 3 pulses
)

# Create a step profile
step_points = analyzer.create_pwl_step(
    current_low=0.0,       # 0A baseline
    current_high=0.8,      # 0.8A step
    step_time=2e-3,        # Step at 2ms
    hold_time=5e-3,        # Hold for 5ms
    total_time=10e-3       # Total 10ms
)
```

## Configuration Parameters

### TransientSetup Parameters

- **`current1`**: Low current level in amps
- **`current2`**: High current level in amps  
- **`pulse_width`**: Pulse high time in seconds
- **`pulse_count`**: Number of pulses
- **`duty_cycle`**: Duty cycle of the pulse (0-1)
- **`rise_time`**: Rise time of the pulse in seconds (200ns minimum)
- **`fall_time`**: Fall time of the pulse in seconds (200ns minimum)
- **`acquisition_time`**: Total acquisition time in seconds
- **`measure_switching_frequency`**: Measure switching frequency before pulse

### TriggerSetup Parameters

- **`channel`**: Trigger channel (0=Vout, 1=Current) - **Use 1 for transient measurements**
- **`level`**: Trigger level in amps when channel=1, volts when channel=0
- **`delay`**: Trigger delay in seconds
- **`timeout`**: Trigger timeout in seconds
- **`slope`**: Trigger slope (0=rising, 1=falling, 2=edge) - **Use 0 for rising edge**
- **`auto`**: Auto trigger mode (True=auto, False=normal)

## Requirements

- LTpowerAnalyzer hardware connected via USB
- LTpowerAnalyzer software installed
- Current probe connected and calibrated
- Python 3.7+ with pythonnet
- Optional: matplotlib for plotting, numpy for data analysis

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check USB connection
   - Verify LTpowerAnalyzer software is installed
   - Close other applications using the device

2. **Transient Initialization Failed**
   - Ensure current probe is connected
   - Check probe calibration
   - Verify probe is not in use by another application

3. **Measurement Failed**
   - Check trigger settings
   - Verify current levels are within probe range (automatic validation will show specific errors)
   - Ensure acquisition time is sufficient
   - Check that probe temperature is not too high

4. **Current Validation Errors**
   - "Current probe is not connected" - Connect appropriate probe
   - "Required current exceeds probe capability" - Reduce current or use higher-rated probe  
   - "Current probe has an error condition" - Check probe connections and calibration
   - "Probe temperature exceeds safe operating limit" - Allow probe to cool down

4. **No Data Captured**
   - Check trigger level and slope
   - Increase trigger timeout
   - Verify trigger channel selection

### Debug Mode

Enable debug mode for detailed information:
```python
analyzer = LTpowerAnalyzer(debug=True)
```

This will print detailed status messages during operation.

## See Also

- Main driver documentation: `../../../Drivers/LTpowerAnalyzerDriver.py`
- Other examples: `../`
- Connection tests: `../ConnectionTest/`