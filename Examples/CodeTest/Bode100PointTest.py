import numpy as np

# Define the bode100_log_points function locally for testing
def bode100_log_points(f_start: float, f_end: float, num_points: int):
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

# Test the bode100_log_points function
if __name__ == "__main__":
    print("Testing bode100_log_points function")
    print("=" * 40)
    print("Note: Testing local copy of the function from LTpowerAnalyzerDriver.py")
    
    # Test with the requested parameters
    f_start = 10
    f_end = 1e6
    num_points = 201
    
    print(f"\nParameters:")
    print(f"  f_start: {f_start} Hz")
    print(f"  f_end: {f_end} Hz")
    print(f"  num_points: {num_points}")
    print()
    
    # Generate the frequency points
    frequencies = bode100_log_points(f_start, f_end, num_points)
    
    print(f"Results:")
    print(f"  Generated {len(frequencies)} frequency points")
    print(f"  First frequency: {frequencies[0]:.6f} Hz")
    print(f"  Last frequency: {frequencies[-1]:.6f} Hz")
    print(f"  Frequency range: {frequencies[0]:.1f} Hz to {frequencies[-1]:.1f} Hz")
    print()
    
    # Show first 10 and last 10 points
    print("First 10 frequencies (Hz):")
    for i in range(min(10, len(frequencies))):
        print(f"  {i+1:3d}: {frequencies[i]:12.6f}")
    
    print("\nLast 10 frequencies (Hz):")
    start_idx = max(0, len(frequencies) - 10)
    for i in range(start_idx, len(frequencies)):
        print(f"  {i+1:3d}: {frequencies[i]:12.6f}")
    
    # Verify logarithmic spacing
    print(f"\nVerification:")
    print(f"  Expected start: {f_start} Hz, Actual start: {frequencies[0]:.6f} Hz")
    print(f"  Expected end: {f_end} Hz, Actual end: {frequencies[-1]:.6f} Hz")
    
    # Check step consistency
    log_step = (np.log10(f_end) - np.log10(f_start)) / (num_points - 1)
    print(f"  Log step: {log_step:.6f}")
    print(f"  Decades covered: {np.log10(f_end) - np.log10(f_start):.2f}")
    
    print("\nTest completed successfully!")