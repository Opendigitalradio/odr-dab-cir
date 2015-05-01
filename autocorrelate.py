#!/usr/bin/env python
#
# Do a single autocorrelation over the whole test.16.14.25.iq file
#
# Licence: see LICENCE file

import numpy as np
import matplotlib.pyplot as pp

file_in = "test.16.14.25.iq"

channel_out = np.fromfile(file_in, np.complex64)

print("Autocorrelating")

correlationlength = 50

def autocorrelate(x, length):
    return np.array([1] + [np.abs(np.corrcoef(x[:-i], x[i:])[0,1]) for i in range(1, length)])

autocorr = autocorrelate(channel_out, correlationlength)

print("Done")

numpeaks = 6
print("The first {} highest peaks are at".format(numpeaks))
print("  index: amplitude")
for ind in autocorr.argsort()[-numpeaks:][::-1]:
    print("   {:4}: {}".format(ind, autocorr[ind]))

fig = pp.figure()
ax = fig.add_subplot(111)
hi = ax.semilogy(autocorr)


pp.show()


