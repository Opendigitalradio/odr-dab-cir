#!/usr/bin/env python
#
# Correlate with the phase reference symbol
#
# Licence: see LICENCE file

import numpy as np
import matplotlib.pyplot as pp
import sys

if len(sys.argv) != 3:
    print("Usage")
    print(" script [f64|u8] <filename>")
    print(" fc64: file is 32-bit float I + 32-bit float Q")
    print(" u8:   file is 8-bit unsigned I + 8-bit unsigned Q")
    sys.exit(1)

print("Reading file")

file_in = sys.argv[2]

if sys.argv[1] == "u8":
    channel_out1 = np.fromfile(file_in, np.uint8)
    print("Convert u8 IQ to fc64 IQ")
    channel_out2 = channel_out1.reshape(2, len(channel_out1)/2)
    channel_out3 = channel_out2[0,...] + 1j * channel_out2[1,...]
    channel_out = channel_out3.astype(np.complex64) / 256.0 - (0.5+0.5j)
elif sys.argv[1] == "fc64":
    channel_out = np.fromfile(file_in, np.complex64)

channel_out = channel_out[0:channel_out.size/2]

print("Reading phase reference")

phase_ref = np.fromfile("phasereference.2048000.fc64.iq", np.complex64)

print("Correlating")

num_correlations = channel_out.size - phase_ref.size
print("{} correlations to do...".format(num_correlations))

correlations = np.array([np.abs(np.corrcoef(channel_out[i:phase_ref.size + i], phase_ref)[0,1]) for i in range(num_correlations)])

print("Done")

numpeaks = 6
print("The first {} highest peaks are at".format(numpeaks))
print("  index: amplitude")
for ind in correlations.argsort()[-numpeaks:][::-1]:
    print("   {:4}: {}".format(ind, correlations[ind]))

fig = pp.figure()
ax = fig.add_subplot(111)
hi = ax.plot(correlations)


pp.show()


