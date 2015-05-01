#!/usr/bin/env python
#
# Do a set of autocorrelations over the test.16.14.25.iq file
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


reshape_width = correlationlength * 4

channel_out_truncated = channel_out[:-(channel_out.size % reshape_width)]

channel_out_reshaped = channel_out_truncated.reshape(channel_out_truncated.size / reshape_width, reshape_width)

channel_autocorr_image = np.zeros((channel_out_reshaped.shape[0], correlationlength))
for i, window in enumerate(channel_out_reshaped):
    if i % 100 == 0:
        print("Window {}".format(i))
    channel_autocorr_image[i] = autocorrelate(window, correlationlength)

rows, cols = channel_autocorr_image.shape

aspect_ratio = 1.0

fig = pp.figure()
ax = fig.add_subplot(111)
hi = ax.imshow(channel_autocorr_image, cmap='hot', aspect=aspect_ratio*(cols/rows))

pp.show()

