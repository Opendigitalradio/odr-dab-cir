#!/usr/bin/env python
#
# Adds additional components to the test.16.iq file, which is
# an array of complex floats, and save it as
# test.16.14.25.iq
#
# Licence: see LICENCE file

import numpy as np
import matplotlib.pyplot as pp

file_in = "test.16.iq"


# Simulate the channel with several components,
# shifted by some number of samples and multiplied by
# the amplitude
#
# The (0, 1.0) component is always present
CIR = [(14, 0.4), (25, 0.3)]

print("Simulate channel {}".format(CIR))

maxdelay = max(delay for delay, ampl in CIR)


original_iq = np.fromfile(file_in, np.complex64)

original_iq_extended = np.append(original_iq, np.zeros(maxdelay, dtype=np.complex64))

channel_out = original_iq_extended

for delay, ampl in CIR:
    print("Add component {}".format(delay))
    channel_out += np.append(np.zeros(delay, dtype=np.complex64), ampl * original_iq_extended[:-delay])


# The simulated channel output is in channel_out

channel_out.tofile("test.16.14.25.iq")

