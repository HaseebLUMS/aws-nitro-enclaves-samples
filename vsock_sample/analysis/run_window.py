import numpy as np
import matplotlib.pyplot as plt

import sys

PERCENTILE = 95
WINDOW_SIZE = 8000

DATAFILES = {
    "2affed_4cpu_1iso.csv": "Pinned CPUs + Isolated",
    "2affed_4cpu.csv": "Pinned CPUs",
    "noaffinity.csv": "Raw",
    "tmp3.csv": "nohz_full isolcpus=domain,managed_irq",
}

def calculate_percentile_latency(latencies, window_size):
    percentiles = []
    for i in range(0, len(latencies), window_size):
        if i == 0: continue
        window = latencies[i:i + window_size]
        percentile = np.percentile(window, PERCENTILE)
        percentiles.append(percentile)
    return percentiles

plt.figure(figsize=(10, 6))

for DATAFILE in DATAFILES:
    latency_data = np.loadtxt(DATAFILE, delimiter=',')
    percentile_latencies = calculate_percentile_latency(latency_data, WINDOW_SIZE)
    plt.plot(percentile_latencies, label=DATAFILES[DATAFILE])

plt.grid()
plt.legend()
plt.xticks([])
plt.xlabel('Time (30 Minutes)')
plt.ylabel(f'{PERCENTILE}th Percentile Latency (\u00B5s)')
plt.title(F'Round Trip Latency For Each {WINDOW_SIZE} Messages Window')

plt.savefig(f"./windows/window.pdf")