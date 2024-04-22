import numpy as np
import matplotlib.pyplot as plt

import sys

DATAFILE = str(sys.argv[1])

# Read latency data from CSV file
latency_data = np.loadtxt(DATAFILE, delimiter=',')

percentiles = list(range(0, 100))
cdf = np.percentile(latency_data, percentiles)

plt.figure(figsize=(10, 6))

plt.plot(cdf, percentiles, color='green')

plt.xlabel('Latency')
plt.ylabel('CDF')
plt.title(F'Round Trip Latency CDF')

plt.savefig(f"./cdf_{DATAFILE}.pdf")