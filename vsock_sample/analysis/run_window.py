import numpy as np
import matplotlib.pyplot as plt

import sys

PERCENTILE = 90
WINDOW_SIZE = 8000

DATAFILE = str(sys.argv[1])

def calculate_percentile_latency(latencies, window_size):
    percentiles = []
    for i in range(0, len(latencies), window_size):
        window = latencies[i:i + window_size]
        percentile = np.percentile(window, PERCENTILE)
        percentiles.append(percentile)
    return percentiles

# Read latency data from CSV file
latency_data = np.loadtxt(DATAFILE, delimiter=',')
percentile_latencies = calculate_percentile_latency(latency_data, WINDOW_SIZE)

plt.figure(figsize=(10, 6))

plt.plot(percentile_latencies, color='green')
plt.grid()

plt.ylim([80.5, 150.5])
plt.xticks([])
plt.xlabel('Time (30 Minutes)')
plt.ylabel(f'{PERCENTILE}th Percentile Latency (\u00B5s)')
plt.title(F'Round Trip Latency For Each {WINDOW_SIZE} Messages Window')

plt.savefig(f"./{DATAFILE}.pdf")