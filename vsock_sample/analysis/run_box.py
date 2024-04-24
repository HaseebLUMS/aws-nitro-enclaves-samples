import numpy as np
import matplotlib.pyplot as plt

import sys

PERCENTILE = 95
WINDOW_SIZE = 8000

COLORS = ["GREEN", "BLACK", "BLUE", "PINK", "MAGENTA"]

DATAFILES = {
    "2affed_4cpu_1iso.csv": "Pinned CPUs + Isolated",
    "2affed_4cpu.csv": "Pinned CPUs",
    "noaffinity.csv": "Raw",
}

def calculate_percentile_latency(latencies, window_size):
    percentiles = []
    for i in range(0, len(latencies), window_size):
        window = latencies[i:i + window_size]
        percentile = np.percentile(window, PERCENTILE)
        percentiles.append(percentile)
    return percentiles

plt.figure(figsize=(10, 6))

for ind, DATAFILE in enumerate(DATAFILES):
    latency_data = np.loadtxt(DATAFILE, delimiter=',')
    percentile_latencies = calculate_percentile_latency(latency_data, WINDOW_SIZE)
    for i in range(0, len(latency_data), WINDOW_SIZE):
        window = latency_data[i:i + WINDOW_SIZE]
        plt.boxplot(window, patch_artist=True)

plt.grid()
plt.legend()
plt.xticks([])
plt.xlabel('Time (30 Minutes)')
plt.ylabel(f'{PERCENTILE}th Percentile Latency (\u00B5s)')
plt.title(F'Round Trip Latency For Each {WINDOW_SIZE} Messages Window')

plt.savefig(f"./boxes/box.pdf")