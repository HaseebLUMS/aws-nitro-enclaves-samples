import numpy as np
import matplotlib.pyplot as plt

import sys

DATAFILES = {
    "2affed_4cpu_1iso.csv": "Pinned CPUs + Isolated",
    "2affed_4cpu.csv": "Pinned CPUs",
    "noaffinity.csv": "Raw",
    "tmp2.csv": "tmp",
}

plt.figure(figsize=(10, 6))

for DATAFILE in DATAFILES:
    # Read latency data from CSV file
    latency_data = np.loadtxt(DATAFILE, delimiter=',')

    percentiles = list(range(0, 100))
    cdf = np.percentile(latency_data[8000:], percentiles)

    plt.plot(cdf, percentiles, label=DATAFILES[DATAFILE])

plt.grid()
plt.legend()
plt.xlabel('Latency (microseconds)')
plt.ylabel('CDF')
plt.title(F'Round Trip Latency CDF')

plt.savefig(f"./cdfs/cdf.pdf")