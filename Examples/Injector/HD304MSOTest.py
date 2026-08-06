import sys
import time

sys.path.insert(0, r"c:\Users\RReay\OneDrive - Analog Devices, Inc\ADI\Projects\LTPowerAnalyzerPython")

from Drivers.InstrumentDriver import HD304MSO

VISA_ADDRESS = "USB0::0x2A8D::0x4704::MY66030161::0::INSTR"


def update_sine_wave(scope, frequency = 1000):
    scope.configure_waveform(channel=1, waveform="SIN", amplitude=2, offset=0.0)
    scope.set_frequency(channel=1, frequency=frequency)
    scope.enable_waveform(channel=1)
    scope.optimize_time_base(frequency)
    #scope.autoscale_vertical_channel(channel=1)

#Main program
scope = HD304MSO(address=VISA_ADDRESS)
if scope.check_connection():
    try:
        print(f"ID: {scope.id}")
        frequency= 10e3
        update_sine_wave(scope, frequency)
        scope.configure_fft(frequency,1)
        scope.configure_fft(frequency,2)
        time.sleep(0.20)
        input_dbv = scope.get_fft_vmax(1)
        output_dbv = scope.get_fft_vmax(2)
        print(f"Input FFT value at {frequency} Hz: {input_dbv}")
        print(f"Output FFT value at {frequency} Hz: {output_dbv}")
    except:
        print("Exception")
    finally:
        scope.close()
else:
    print("Failed to connect to the HD304MSO.")


