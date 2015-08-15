#!/usr/bin/env python
#
# Do a set of autocorrelations over the test.16.14.25.iq file
#
# Licence: see LICENCE file
#
# hackrf_transfer example:
# hackrf_transfer -r hackrf_dab.iq -f 211648000 -s 8 -n 768000

import numpy as np
import matplotlib.pyplot as pp
import sys

if len(sys.argv) != 3:
    print("Usage")
    print(" script [f64|u8] <filename>")
    print(" fc64: file is 32-bit float I + 32-bit float Q")
    print(" u8:   file is 8-bit unsigned I + 8-bit unsigned Q")
    sys.exit(1)

file_in = sys.argv[2]

if sys.argv[1] == "u8":
    channel_out1 = np.fromfile(file_in, np.uint8)
    print("Convert u8 IQ to fc64 IQ")
    channel_out2 = channel_out1.reshape(2, len(channel_out1)/2)
    channel_out3 = channel_out2[0,...] + 1j * channel_out2[1,...]
    channel_out = channel_out3.astype(np.complex64) / 256.0 - (0.5+0.5j)
elif sys.argv[1] == "fc64":
    channel_out = np.fromfile(file_in, np.complex64)

channel_out = channel_out[:channel_out.size / 4]

print("Autocorrelating")

correlationlength = 500

def autocorrelate(x, length):
    return np.array([1] + [np.abs(np.corrcoef(x[:-i], x[i:])[0,1]) for i in range(1, length)])


reshape_width = correlationlength * 4

channel_out_truncated = channel_out[:channel_out.size - (channel_out.size % reshape_width)]

channel_out_reshaped = channel_out_truncated.reshape(channel_out_truncated.size / reshape_width, reshape_width)

channel_autocorr_image = np.zeros((channel_out_reshaped.shape[0], correlationlength))

num_windows = len(channel_out_reshaped)

for i, window in enumerate(channel_out_reshaped):
    if i % 100 == 0:
        print("Window {}/{}".format(i, num_windows))
    channel_autocorr_image[i] = autocorrelate(window, correlationlength)

rows, cols = channel_autocorr_image.shape

print("Shape: {}x{}".format(rows, cols))

aspect_ratio = 1.0

fig = pp.figure()
ax = fig.add_subplot(111)
hi = ax.imshow(channel_autocorr_image, cmap='hot', aspect=aspect_ratio*(cols/rows))

fig2 = pp.figure()
ax = fig2.add_subplot(211)
accumulated0 = channel_autocorr_image.sum(axis=0)
ac1 = ax.plot(accumulated0)

ax = fig2.add_subplot(212)
accumulated1 = channel_autocorr_image.sum(axis=1)
ac1 = ax.plot(accumulated1)

pp.show()

