#!/usr/bin/env python3
"""
Spike Detection Analysis for LNA Noise Density Data
Identifies significant spikes in noise density measurements using multiple detection methods.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_data(filename):
    """Load CSV data skipping header comments."""
    # Find where actual data starts (after comments)
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    data_start = 0
    for i, line in enumerate(lines):
        if not line.startswith('#') and ',' in line:
            data_start = i
            break
    
    # Read the CSV data
    df = pd.read_csv(filename, skiprows=data_start)
    return df

def find_spikes_statistical(data, method='zscore', threshold=3.0):
    """Find spikes using statistical methods."""
    values = data['lna_input_noise_density'].values
    
    if method == 'zscore':
        # Standard Z-score method
        mean_val = np.mean(values)
        std_val = np.std(values)
        z_scores = np.abs((values - mean_val) / std_val)
        spike_mask = z_scores > threshold
        return spike_mask, z_scores
    
    elif method == 'modified_zscore':
        # Modified Z-score using median
        median_val = np.median(values)
        mad = np.median(np.abs(values - median_val))
        modified_z_scores = 0.6745 * (values - median_val) / mad
        spike_mask = np.abs(modified_z_scores) > threshold
        return spike_mask, modified_z_scores
    
    elif method == 'iqr':
        # Interquartile range method
        Q1 = np.percentile(values, 25)
        Q3 = np.percentile(values, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        spike_mask = (values < lower_bound) | (values > upper_bound)
        # Calculate "IQR scores" for consistency
        iqr_scores = np.maximum(
            (lower_bound - values) / IQR,
            (values - upper_bound) / IQR
        )
        iqr_scores = np.maximum(iqr_scores, 0)  # Only positive scores
        return spike_mask, iqr_scores

def find_spikes_amplitude_ratio(data, min_ratio=2.0, window_size=5):
    """Find spikes based on amplitude ratio to surrounding points."""
    values = data['lna_input_noise_density'].values
    frequencies = data['frequency'].values
    
    spikes = []
    
    for i in range(window_size, len(values) - window_size):
        current_val = values[i]
        
        # Get surrounding values (excluding current point)
        left_vals = values[i-window_size:i]
        right_vals = values[i+1:i+window_size+1]
        surrounding_vals = np.concatenate([left_vals, right_vals])
        
        # Calculate ratio to median of surrounding values
        median_surrounding = np.median(surrounding_vals)
        if median_surrounding > 0:
            ratio = current_val / median_surrounding
            if ratio >= min_ratio:
                spikes.append({
                    'index': i,
                    'frequency': frequencies[i],
                    'value': current_val,
                    'median_surrounding': median_surrounding,
                    'ratio': ratio
                })
    
    return spikes

def analyze_spikes(filename):
    """Comprehensive spike analysis."""
    print(f"Loading data from: {filename}")
    df = load_data(filename)
    
    print(f"Total data points: {len(df)}")
    print(f"Frequency range: {df['frequency'].min():.2f} Hz to {df['frequency'].max():.2f} Hz")
    print(f"Noise density range: {df['lna_input_noise_density'].min():.2e} to {df['lna_input_noise_density'].max():.2e} V/√Hz")
    print()
    
    # Statistical spike detection
    print("=== Statistical Spike Detection ===")
    
    methods = [
        ('Z-Score', 'zscore', 3.0),
        ('Modified Z-Score', 'modified_zscore', 3.0),
        ('IQR', 'iqr', 1.5)
    ]
    
    all_statistical_spikes = []
    
    for name, method, threshold in methods:
        spike_mask, scores = find_spikes_statistical(df, method, threshold)
        spike_indices = np.where(spike_mask)[0]
        
        print(f"\n{name} method (threshold={threshold}):")
        print(f"  Found {len(spike_indices)} spikes")
        
        if len(spike_indices) > 0:
            for idx in spike_indices:
                freq = df.iloc[idx]['frequency']
                value = df.iloc[idx]['lna_input_noise_density']
                score = scores[idx]
                print(f"    {freq:8.2f} Hz: {value:.3e} V/√Hz (score: {abs(score):.2f})")
                all_statistical_spikes.append(idx)
    
    # Amplitude ratio spike detection
    print(f"\n=== Amplitude Ratio Spike Detection ===")
    amplitude_spikes = find_spikes_amplitude_ratio(df, min_ratio=2.0, window_size=5)
    
    print(f"Found {len(amplitude_spikes)} amplitude spikes (ratio ≥ 2.0):")
    for spike in amplitude_spikes:
        print(f"  {spike['frequency']:8.2f} Hz: {spike['value']:.3e} V/√Hz (ratio: {spike['ratio']:.2f}x)")
    
    # Find consensus spikes (detected by multiple methods)
    print(f"\n=== Consensus Analysis ===")
    amplitude_indices = [spike['index'] for spike in amplitude_spikes]
    
    # Find indices that appear in both statistical and amplitude methods
    consensus_indices = set(all_statistical_spikes) & set(amplitude_indices)
    
    print(f"Spikes detected by both statistical and amplitude methods: {len(consensus_indices)}")
    for idx in sorted(consensus_indices):
        freq = df.iloc[idx]['frequency']
        value = df.iloc[idx]['lna_input_noise_density']
        # Find the amplitude spike info
        amp_spike = next(s for s in amplitude_spikes if s['index'] == idx)
        print(f"  {freq:8.2f} Hz: {value:.3e} V/√Hz (ratio: {amp_spike['ratio']:.2f}x)")
    
    # Create visualization
    create_spike_visualization(df, amplitude_spikes, all_statistical_spikes, consensus_indices)
    
    return df, amplitude_spikes, all_statistical_spikes, consensus_indices

def create_spike_visualization(df, amplitude_spikes, statistical_spike_indices, consensus_indices):
    """Create comprehensive spike visualization."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    frequencies = df['frequency'].values
    values = df['lna_input_noise_density'].values
    
    # Plot 1: Overview with all spikes
    ax1.loglog(frequencies, values, 'b-', alpha=0.7, linewidth=1, label='Noise Density')
    
    # Mark amplitude spikes
    for spike in amplitude_spikes:
        ax1.loglog(spike['frequency'], spike['value'], 'ro', markersize=8, alpha=0.7)
    
    # Mark consensus spikes with different marker
    for idx in consensus_indices:
        freq = df.iloc[idx]['frequency']
        value = df.iloc[idx]['lna_input_noise_density']
        ax1.loglog(freq, value, 's', color='purple', markersize=10, alpha=0.8)
    
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Noise Density (V/√Hz)')
    ax1.set_title('Spike Detection Overview')
    ax1.grid(True, alpha=0.3)
    ax1.legend(['Noise Density', 'Amplitude Spikes', 'Consensus Spikes'])
    
    # Plot 2: Linear scale focusing on spike amplitudes
    ax2.semilogy(frequencies, values, 'b-', alpha=0.7, linewidth=1)
    
    for spike in amplitude_spikes:
        ax2.semilogy(spike['frequency'], spike['value'], 'ro', markersize=8, alpha=0.7)
    
    for idx in consensus_indices:
        freq = df.iloc[idx]['frequency']
        value = df.iloc[idx]['lna_input_noise_density']
        ax2.semilogy(freq, value, 's', color='purple', markersize=10, alpha=0.8)
    
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Noise Density (V/√Hz)')
    ax2.set_title('Linear Frequency Scale View')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Amplitude ratios
    if amplitude_spikes:
        spike_freqs = [s['frequency'] for s in amplitude_spikes]
        spike_ratios = [s['ratio'] for s in amplitude_spikes]
        
        ax3.semilogx(spike_freqs, spike_ratios, 'ro', markersize=8, alpha=0.7)
        ax3.axhline(y=2.0, color='r', linestyle='--', alpha=0.5, label='Detection Threshold')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Amplitude Ratio')
        ax3.set_title('Spike Amplitude Ratios')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
    
    # Plot 4: Distribution of noise density values
    ax4.hist(values, bins=50, alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Noise Density (V/√Hz)')
    ax4.set_ylabel('Count')
    ax4.set_title('Noise Density Distribution')
    ax4.grid(True, alpha=0.3)
    
    # Mark spike values in histogram
    for spike in amplitude_spikes:
        ax4.axvline(spike['value'], color='red', alpha=0.5, linestyle='--')
    
    plt.tight_layout()
    plt.show()
    
    # Save the plot
    plt.savefig('spike_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\nPlot saved as: spike_analysis.png")

if __name__ == "__main__":
    # Analyze the data file
    filename = "Data/LNANoiseDensity_2025-10-22_105219.csv"
    df, amplitude_spikes, statistical_spikes, consensus_spikes = analyze_spikes(filename)
    
    print(f"\n=== Summary ===")
    print(f"Total amplitude spikes found: {len(amplitude_spikes)}")
    print(f"Statistical spike detections: {len(statistical_spikes)}")
    print(f"High-confidence consensus spikes: {len(consensus_spikes)}")