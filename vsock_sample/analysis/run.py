import numpy as np
import matplotlib.pyplot as plt

PERCENTILE = 90
WINDOW_SIZE = 10000

DATAFILE = 'records.csv'

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

plt.xticks([])
plt.xlabel('Time (60 Minutes)')
plt.ylabel(f'{PERCENTILE}th Percentile Latency (\u00B5s)')
plt.title(F'Round Trip Latency For Each {WINDOW_SIZE} Messages Window')

plt.savefig("./result.pdf")