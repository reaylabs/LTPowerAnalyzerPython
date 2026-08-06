import sys
import time
import os
import csv
import msvcrt

# Add the root project directory and Drivers directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
drivers_dir = os.path.join(project_root, 'Drivers')
sys.path.insert(0, project_root)
sys.path.insert(0, drivers_dir)

#import the drivers
from Drivers.InstrumentDriver import HD304MSO
from Drivers.LNAmplifierDriver import LNAmplifier
from Drivers.Utilites import generate_log_frequencies

#constants
CYCLE_COUNT = 50
FFT_WINDOW_SIZE = 0.5
LNA_GAIN_INDEX = 1 #60dB
LNA_FILTER_INDEX = 2 #1Mhz
LNA_PORT_INDEX = 0
LNA_PRINT_STATUS = True
MIN_FILTER_INDEX = 2 #1Mhz
PRINT_GAINS = True
START_FREQUENCY = 10
STOP_FREQUENCY = 1e6
POINT_COUNT = 21
VISA_ADDRESS = "USB0::0x2A8D::0x4704::MY66030161::0::INSTR"
SAVE_CSV = True
INJECTION_AMPLITUDE = 2.0

def interpolate_lna_gain(frequencies, gain_data, frequency):
    """
    Returns the interpolated LNA gain at the given frequency using linear interpolation.

    :param frequencies: List of calibration frequencies in Hz.
    :param gain_data: List of gain values in dB corresponding to frequencies.
    :param frequency: Target frequency in Hz.
    :return: Interpolated gain in dB.
    """
    if frequency <= frequencies[0]:
        return gain_data[0]
    if frequency >= frequencies[-1]:
        return gain_data[-1]

    for i in range(len(frequencies) - 1):
        if frequencies[i] <= frequency <= frequencies[i + 1]:
            t = (frequency - frequencies[i]) / (frequencies[i + 1] - frequencies[i])
            return gain_data[i] + t * (gain_data[i + 1] - gain_data[i])

    return gain_data[-1]


def update_sine_wave(scope, frequency = 1000):
    scope.configure_waveform(channel=1, waveform="SIN", amplitude=INJECTION_AMPLITUDE, offset=0.0)
    scope.set_frequency(channel=1, frequency=frequency)
    scope.enable_waveform(channel=1)
    #scope.autoscale_vertical_channel(channel=2)
    scope.optimize_time_base(frequency,CYCLE_COUNT)

#Main program

# Connect to LNAmplifier
lna_open = False
lna = LNAmplifier("LNAmplifier")
lna.open_all_devices(LNA_PRINT_STATUS)
lna_open = True
lna.set_gain(LNA_GAIN_INDEX, LNA_PORT_INDEX)
lna.set_filter(LNA_FILTER_INDEX, LNA_PORT_INDEX)

# Read gain vs frequency data from EEPROM
gain_frequencies = lna.get_eeprom_dataset(0, LNA_PORT_INDEX)
eeprom_gain_index = LNA_FILTER_INDEX + (LNA_GAIN_INDEX-1)*4
gain_data = lna.get_eeprom_dataset(eeprom_gain_index, LNA_PORT_INDEX)

if gain_frequencies is not None and gain_data is not None:
    if (PRINT_GAINS):
        print(f"EEPROM data: {len(gain_frequencies)} frequency points, {len(gain_data)} gain points")
        for i in range(len(gain_frequencies)):
            print(f"  {gain_frequencies[i]:.1f} Hz: {gain_data[i]:.2f} dB")
else:
    print("Failed to read EEPROM gain data.")

# Connect to scope
scope_open = False
scope = HD304MSO(address=VISA_ADDRESS)
scope._timeout = 40000
if not scope.check_connection():
    print("Failed to connect to the HD304MSO. Exiting.")
    lna.close()

csv_filename = os.path.join(os.path.dirname(__file__), "PSRR_results.csv")
results = []
aborted = False

try:
    scope_open = True
    print(f"ID: {scope.id}")
    print("Press 'q' at any time to stop.\n")
    print(f"{'Frequency (Hz)':<16}{'Input FFT (dBV)':<18}{'Output FFT (dBV)':<18}{'LNA Gain (dB)':<16}{'PSRR (dB)':<12}")
    print(f"{'-'*80}")

    #frequencies = generate_log_frequencies(START_FREQUENCY, STOP_FREQUENCY, POINT_COUNT)
    frequencies = [
        10, 20, 30, 40, 50, 60, 70, 80, 90,
        100, 200, 300, 400, 500, 600, 700, 800, 900,
        1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
        10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000,
        1000000
    ]
    #frequencies = [10,100,1000,10e3,100e3,1e6]
    #frequencies = [100]
    #setup the filter
    filter_index = 1
    old_filter_index = 1

    for frequency in frequencies:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'q', b'Q'):
                print("\nStopped by user.")
                aborted = True
                break

        #set the filter
        if frequency < 20e3:
            filter_index = 4 
        elif frequency < 80e3:
            filter_index = 3 
        elif frequency < 1.001e6:
            filter_index = 2 
        else: 
            filter_index = 1 
        if filter_index < MIN_FILTER_INDEX:
            filter_index = MIN_FILTER_INDEX
        if filter_index != old_filter_index:
            lna.set_filter(filter_index,LNA_PORT_INDEX)
            old_filter_index = filter_index

        #scope.set_acquire_averaging(32)
        update_sine_wave(scope, frequency)
        scope.configure_fft(frequency, 1, FFT_WINDOW_SIZE)
        scope.configure_fft(frequency, 2, FFT_WINDOW_SIZE)
        input_dbv = float(scope.get_fft_vmax(1))
        output_dbv = float(scope.get_fft_vmax(2))
        lna_gain = interpolate_lna_gain(gain_frequencies, gain_data, frequency)
        psrr = (lna_gain + abs(output_dbv)) - abs(input_dbv)
        results.append([f"{frequency:.1f}", f"{input_dbv:.2f}", f"{output_dbv:.2f}", f"{lna_gain:.2f}", f"{psrr:.2f}"])
        print(f"{frequency:<16.1f}{input_dbv:<18.2f}{output_dbv:<18.2f}{lna_gain:<16.2f}{psrr:<12.2f}", flush=True)
except Exception as e:
    aborted = True
    print(f"Exception: {e}")
finally:
    if SAVE_CSV and not aborted:
        with open(csv_filename, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Frequency (Hz)", "Input FFT (dBV)", "Output FFT (dBV)", "LNA Gain (dB)", "PSRR (dB)"])
            csv_writer.writerows(results)
        print(f"\nResults saved to: {csv_filename}")
    elif aborted:
        print("\nCSV not saved (measurement aborted).")
    if (scope_open):
        scope.close()
    if (lna_open):
        lna.close()


