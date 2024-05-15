import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['font.size'] = 15
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#1f77b4', '#2ca02c', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'])


import sys

PERCENTILE = 90
WINDOW_SIZE = 8000

DATAFILES = {
    # "2affed_4cpu_1iso.csv": "Pinned CPUs + Isolated",
    # "2affed_4cpu.csv": "Pinned CPUs",
    "unoptimized.csv": "Without Optimizations",
    # "tmp3.csv": "nohz_full isolcpus=domain,managed_irq",
    "optimized.csv": "With Low-Jitter Optimization",
}

LINE_STYLES = ['dotted', 'solid']
COLORS = ['b', 'g']

def calculate_percentile_latency(latencies, window_size):
    percentiles = []
    for i in range(0, len(latencies), window_size):
        if i == 0: continue
        window = latencies[i:i + window_size]
        percentile = np.percentile(window, PERCENTILE)
        percentiles.append(percentile)
    return percentiles

plt.figure(figsize=(10, 6))

for ind, DATAFILE in enumerate(DATAFILES):
    latency_data = np.loadtxt(DATAFILE, delimiter=',')
    percentile_latencies = calculate_percentile_latency(latency_data, WINDOW_SIZE)
    plt.plot(percentile_latencies, label=DATAFILES[DATAFILE], color=COLORS[ind], linestyle=LINE_STYLES[ind])

plt.grid()
plt.legend()
plt.xticks([])
plt.xlabel('Time (30 Minutes)')
plt.ylabel(f'{PERCENTILE}th Percentile Latency (\u00B5s)')
plt.title(F'Round Trip Latency For Each {WINDOW_SIZE} Messages Window')

plt.tight_layout()
plt.savefig(f"./windows/window.pdf")
