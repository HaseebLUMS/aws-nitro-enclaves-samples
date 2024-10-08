import numpy as np
import matplotlib.pyplot as plt

import matplotlib as mpl

mpl.rcParams['font.size'] = 15
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#1f77b4', '#2ca02c', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'])

mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42

import sys

DATAFILES = {
    # "2affed_4cpu_1iso.csv": "Pinned CPUs + Isolated",
    #"2affed_4cpu.csv": "Pinned CPUs",
    # "unoptimized.csv": "Without Optimizations",
    #"tmp3.csv": "nohz_full isolcpus=domain,managed_irq",
    "optimized.csv": "With Low-Jitter Optimization",
    }


LINE_STYLES = ['dotted', 'solid']
COLORS = ['b', 'g']

# plt.figure(figsize=(10, 6))

for ind, DATAFILE in enumerate(DATAFILES):
    ind = 1
    # Read latency data from CSV file
    latency_data = np.loadtxt(DATAFILE, delimiter=',')

    percentiles = list(range(0, 100))
    cdf = np.percentile(latency_data, percentiles)

    print("For ", DATAFILE)
    res = round(np.percentile(latency_data, 90) - np.percentile(latency_data, 0), 2)
    print("Difference between 90th percentile and 0th percentile", res)

    plt.plot(cdf, percentiles, color=COLORS[ind], linestyle=LINE_STYLES[ind])
    # plt.plot(cdf, percentiles, label=f"{DATAFILES[DATAFILE]}", color=COLORS[ind], linestyle=LINE_STYLES[ind])

# plt.grid()
# plt.legend()
plt.xlabel('Latency (\u00B5s)', fontsize=16)
plt.ylabel('CDF')
# plt.title(F'Round Trip Latency CDF')

plt.tight_layout()
plt.savefig(f"./cdfs/tee_cdf.pdf")
