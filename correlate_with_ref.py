#!/usr/bin/env python
#
# Correlate with the phase reference symbol
#
# Licence: see LICENCE file

import numpy as np
import matplotlib.pyplot as pp
import sys

if len(sys.argv) < 2:
    print("Usage")
    print(" script [fc64|u8] <filename> [<figure filename>]")
    print(" fc64: file is 32-bit float I + 32-bit float Q")
    print(" u8:   file is 8-bit unsigned I + 8-bit unsigned Q")
    print(" if <figure filename> is given, save the figure instead of showing it")
    sys.exit(1)

print("Reading file")

file_in = sys.argv[2]

if sys.argv[1] == "u8":
    channel_out1 = np.fromfile(file_in, np.uint8)
    print("Convert u8 IQ to fc64 IQ")
    channel_out2 = channel_out1.reshape(2, int(len(channel_out1)/2))
    channel_out3 = channel_out2[0,...] + 1j * channel_out2[1,...]
    channel_out = channel_out3.astype(np.complex64) / 256.0 - (0.5+0.5j)
elif sys.argv[1] == "fc64":
    channel_out = np.fromfile(file_in, np.complex64)

file_figure = None
if len(sys.argv) == 4:
    file_figure = sys.argv[3]

print("  File contains {} samples ({}ms)".format(
    len(channel_out), len(channel_out) / 2048000.0))

# T = 1/2048000 s
# NULL symbol is 2656 T (about 1.3ms) long.
T_NULL = 2656
# Full transmission frame in TM1 is 96ms = 196608 T.
T_TF = 196608

print("Reading phase reference")
phase_ref = np.fromfile("phasereference.2048000.fc64.iq", np.complex64)

def calc_cir(channel, start_ix):
    """Calculate correlation with phase reference"""

    channel_out


    # As we do not want to correlate of the whole recording that might be
    # containing several transmission frames, we first look for the null symbol in the
    # first 96ms
    print("Searching for NULL symbol")

    # Calculate power on blocks of length 2656 over the first 96ms. To gain speed,
    # we move the blocks by N samples.
    N = 20
    channel_out_power = np.array([np.abs(channel[start_ix+t:start_ix+t+T_NULL]).sum() for t in range(0, T_TF-T_NULL, N)])

    # Look where the power is smallest, this gives the index where the NULL starts.
    # Because if the subsampling, we need to multiply the index.
    t_null = N * channel_out_power.argmin()

    print("  NULL symbol starts at ix={}".format(t_null))

    # The synchronisation channel occupies 5208 T and contains NULL symbol and
    # phase reference symbol. The phase reference symbol is 5208 - 2656 = 2552 T
    # long.
    if len(phase_ref) != 2552:
        print("Warning: phase ref len is {} != 2552".format(len(phase_ref)))


    # We want to correlate our known phase reference symbol against the received
    # signal, and give us some more margin about the exact position of the NULL
    # symbol.
    print("Correlating")

    # We start a bit earlier than the end of the null symbol
    corr_start_ix = t_null + T_NULL - 50

    # In TM1, the longest spacing between carrier components one can allow is
    # around 504 T (246us, or 74km at speed of light). This gives us a limit
    # on the number of correlations it makes sense to do.
    max_component_delay = 1000 # T

    cir = np.array([np.abs(np.corrcoef(channel[start_ix + corr_start_ix + i:start_ix + corr_start_ix + phase_ref.size + i], phase_ref)[0,1]) for i in range(max_component_delay)])

    # In order to be able to compare measurements accross transmission frames,
    # we normalise the CIR against channel power
    channel_power = np.abs(channel[start_ix:start_ix+T_TF]).sum()

    return cir / channel_power

num_correlations = int(len(channel_out) / T_TF)
print("Doing {} correlations".format(num_correlations))

cirs = np.array([
    calc_cir(channel_out, i * T_TF)
    for i in range(num_correlations) ])

print("Plotting")

pp.subplot(211)
pp.plot(cirs.sum(axis=0))
pp.subplot(212)
pp.imshow(cirs)

print("Done")

if file_figure:
    pp.savefig(file_figure)
else:
    pp.show()



