# Changelog for LTpowerAnalyzerPython

## [0.0.14] - 2026-02-08
### Added
1. LNA files now have option to not save data to files.
2. LNA calibration file now doesn't timeout on bode100 first communication.


## [0.0.13] - 2026-02-04
### Added
1. Update LNA files.

## [0.0.12] - 2026-01-29
### Added
- **Transient Measurement Functionality**: Complete implementation of transient measurement capabilities
  - `initialize_transient_measurement()`: Initialize transient measurement system
  - `execute_transient_measurement()`: Execute step transient measurements
  - `execute_pwl_transient_measurement()`: Execute Piece-Wise Linear transient measurements
  - `TransientSetup` and `PWLPoint` configuration classes
  - PWL utility functions: `create_pwl_step()`, `create_pwl_ramp()`, `create_pwl_pulse_train()`
- **Current Probe Validation and Safety**: Automatic validation for all probe types (1A, 10A, 50A, 100A)
  - Current probe connection detection and capability checking
  - Automatic validation of requested current levels against probe limits
  - Temperature monitoring and error condition detection
  - `get_current_probe_info()` for comprehensive probe information
- **Enhanced Trigger Configuration**: Optimized triggering for transient measurements
  - Automatic trigger level calculation (50% of maximum current)
  - Current waveform triggering (channel=1) with rising edge detection
- **Examples and Documentation**:
  - `TransientMeasurementExample.py`: Complete demonstration with data export and plotting
  - `TransientConnectionTest.py`: Validation and testing script
  - Comprehensive README with usage examples and troubleshooting

## [0.0.11] - 2025-12-20
### Added
- Added LNA3 support in the calibration programs and LNAmplifierDriver
- More calibration runs

## [0.0.10] - 2025-11-20
### Added
- Update the Calibration program to go from 10 to 10Mhz
- More calibration runs

## [0.0.9] - 2025-11-7
### Added
- Added the LTPowerAnalyzer Input Noise Density measurement

## [0.0.8] - 2025-11-6
### Added
- Added the LNA2 first measurements

## [0.0.7] - 2025-10-26
### Added
- Ability to set LNANoiseDensity plot name
- LTC83401 6Mhz noise plot

## [0.0.6] - 2025-10-21
### Added
- LNANoiseDensity.py working.

## [0.0.5] - 2025-10-20
### Added
- Updated LNADriver and examples
- Read and Write to EEPROM working

## [0.0.4] - 2025-10-19
### Added
- Updated LNADriver and examples

## [0.0.3] - 2025-10-18
### Added
- Bode GainPhase complete
- Started working on the LNAmplifier
- Added the Utilities folder

## [0.0.2] - 2025-10-17
### Added
- Added RL2000 example
- Added the Bode100 examples
- Made changes to the InstrumentDriver.py to make the Bode100 examples work.

## [0.0.1] - 2025-10-12
### Added
- Initial Python library creation
- LTpowerAnalyzer Python wrapper for .NET driver
- Connection test example
- Basic project structure and documentation
