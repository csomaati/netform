(TRACE, TRACE_LEN, SH_LEN, SH_COUNT, SH_OK, VF_COUNT, VF_OK, ALL_COUNT, ALL_OK,
PREDICTION_COUNT, PREDICTION_OK, IS_VF, SH_ROUTES, VF_ROUTES, ALL_ROUTES, TRACE_STR) = range(0, 16)
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib import pyplot as plt
from matplotlib import mlab
import pylab as pl
import json
from tools import helpers
from scipy import stats

with open('/mnt/ADAT/measurements3/data/foodweb/results/prediction_caida_rank') as f:
    data = json.load(f)

with open('/tmp/tmp1') as f:
    data = json.load(f)

# k1 = [x[PREDICTION_COUNT] for x in data if x[PREDICTION_OK]]
# k2 = [x[VF_COUNT] for x in data if x[VF_OK]]
# k3 = [x[SH_COUNT] for x in data if x[SH_OK]]
# k4 = [x[ALL_COUNT] for x in data if x[ALL_OK]]
k1 = [x[PREDICTION_COUNT] for x in data]
k2 = [x[VF_COUNT] for x in data]
k3 = [x[SH_COUNT] for x in data]
k4 = [x[ALL_COUNT] for x in data]
h1 = sorted(k1)
h2 = sorted(k2)
h3 = sorted(k3)
h4 = sorted(k4)

grp1, bin1 = np.histogram(h1, bins=range(0, max(h1)+1), density=False)
grp2, bin2 = np.histogram(h2, bins=range(0, max(h2)+1), density=False)
grp3, bin3 = np.histogram(h3, bins=range(0, max(h3)+1), density=False)
grp4, bin4 = np.histogram(h4, bins=range(0, max(h4)+1), density=False)

hist1, bin1 = np.histogram(h1, bins=range(0, max(h1)+1), density=True)
hist2, bin2 = np.histogram(h2, bins=range(0, max(h2)+1), density=True)
hist3, bin3 = np.histogram(h3, bins=range(0, max(h3)+1), density=True)
hist4, bin4 = np.histogram(h4, bins=range(0, max(h4)+1), density=True)

# # PDF plot in log-log scale
# l1, = plt.loglog(range(1, max(h1)+1), hist1, '-o')
# l2, = plt.loglog(range(1, max(h2)+1), hist2, '-o')
# l3, = plt.loglog(range(1, max(h3)+1), hist3, '-o')
# l4, = plt.loglog(range(1, max(h4)+1), hist4, '-o')

cs1 = np.cumsum(grp1) / float(len(h1))
cs2 = np.cumsum(grp2) / float(len(h2))
cs3 = np.cumsum(grp3) / float(len(h3))
cs4 = np.cumsum(grp4) / float(len(h4))

# ECDF plot
l1, = plt.plot(range(0, max(h1)), cs1, '-o', sety)
l2, = plt.plot(range(0, max(h2)), cs2, '--')
l3, = plt.plot(range(0, max(h3)), cs3, '-')
l4, = plt.plot(range(0, max(h4)), cs4)

plt.legend((l1, l2, l3, l4), ('GOOD', 'VF', 'SH', 'ALL'), loc='lower right')
plt.xlim(0, 3000)
plt.set_yscale('log')
# plt.ylim(0, 0.002)
plt.show()
