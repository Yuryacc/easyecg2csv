#!/usr/bin/env python3
"""
parse_pc80b_with_png.py
parse_pc80b_v5_12bit_header_trailer_masked.py - name modified by Yury

PC-80B .dat file parser with non-waveform detection.

Features:
- Parameters: header-size, trailer-size, samplerate
- Extracts 12-bit ECG samples (ignores upper 4 bits = quality flags)
- Detects non-waveform regions using min/max thresholds:
    * Outlier = < 70% of min_signal OR > 130% of max_signal
- In flagged regions:
    * Set upper 4 bits (quality) = 0
    * Set lower 12 bits (amplitude) = int(0.7 * min_signal)
- Saves:
    1. CSV with all samples (index, time, amplitude, quality_flag)
    2. CSV with zeroed interval log
    3. PNG waveform plot with zeroed regions visible
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_file_bytes(path):
    with open(path, "rb") as f:
        return bytearray(f.read())  # mutable


def process_file(path, header_size, trailer_size, sample_rate, output_prefix=None):
    data = read_file_bytes(path)
    size = len(data)
    print(f"Loaded {path}, size={size} bytes")

    # --- Header
    header = data[:header_size]

    # --- Tail as uint16 little-endian
    tail = data[header_size:]
    if len(tail) % 2 != 0:
        tail = tail[:-1]
    samples = np.frombuffer(tail, dtype="<u2", offset=0).copy()  # mutable

    n_per_20s = sample_rate * 20
    idx = 0
    zeroed_regions = []

    while idx + n_per_20s < len(samples):
        # Step 2: baseline min/max
        window = samples[idx:idx+n_per_20s] & 0x0FFF
        min_signal = np.min(window)
        max_signal = np.max(window)

        # Step 3: thresholds
        low_thresh = 0.7 * min_signal
        high_thresh = 1.3 * max_signal

        outliers = np.where((samples[idx+n_per_20s:] & 0x0FFF < low_thresh) |
                            (samples[idx+n_per_20s:] & 0x0FFF > high_thresh))[0]

        if outliers.size == 0:
            break
        first_outlier = idx + n_per_20s + outliers[0]

        # Step 4: overwrite region
        region_bytes = header_size + trailer_size
        region_samples = region_bytes // 2
        end_idx = min(first_outlier + region_samples, len(samples))

        replacement_value = int(0.7 * min_signal) & 0x0FFF
        samples[first_outlier:end_idx] = replacement_value  # only 12 bits, high bits already ignored

        zeroed_regions.append((first_outlier, end_idx, replacement_value))
        idx = end_idx

    # --- Build CSV data
    times = np.arange(len(samples)) / float(sample_rate)
    amplitudes = samples & 0x0FFF
    flags = (samples >> 12) & 0x000F

    df = pd.DataFrame({
        "sample_index": np.arange(len(samples)),
        "time_s": times,
        "amplitude_12bit": amplitudes.astype(int),
        "quality_flag": flags.astype(int)
    })

    base = output_prefix or os.path.splitext(os.path.basename(path))[0]
    csv_out = base + "_parsed.csv"
    df.to_csv(csv_out, index=False)
    print(f"Saved parsed CSV: {csv_out}")

    # --- Interval log CSV
    intervals = []
    for start, end, val in zeroed_regions:
        intervals.append({
            "start_sample": start,
            "end_sample": end,
            "start_s": start / sample_rate,
            "end_s": end / sample_rate,
            "duration_s": (end - start) / sample_rate,
            "replacement_value": val
        })

    if intervals:
        df_int = pd.DataFrame(intervals)
        intervals_out = base + "_intervals.csv"
        df_int.to_csv(intervals_out, index=False)
        print(f"Saved intervals CSV: {intervals_out}")
    else:
        print("No non-waveform regions detected.")

    # --- Plot waveform
    plt.figure(figsize=(12, 4))
    plt.plot(times, amplitudes, linewidth=0.7, label="ECG signal")
    plt.title(f"{base} — {len(samples)} samples @ {sample_rate} Hz")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (12-bit units)")
    plt.tight_layout()

    png_out = base + "_waveform.png"
    plt.savefig(png_out, dpi=150)
    print(f"Saved waveform PNG: {png_out}")


def main():
    ap = argparse.ArgumentParser(description="PC-80B parser with CSV + PNG output")
    ap.add_argument("file", help="Input .dat file")
    ap.add_argument("--header-size", type=int, default=512,
                    help="Header size in bytes (default 512)")
    ap.add_argument("--trailer-size", type=int, default=512,
                    help="Trailer size in bytes (default 512)")
    ap.add_argument("--samplerate", type=int, default=150,
                    help="Sample rate in Hz (default 150)")
    ap.add_argument("--output-prefix", default=None,
                    help="Prefix for output files")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print("Error: file not found:", args.file)
        sys.exit(1)

    process_file(args.file,
                 header_size=args.header_size,
                 trailer_size=args.trailer_size,
                 sample_rate=args.samplerate,
                 output_prefix=args.output_prefix)


if __name__ == "__main__":
    main()

