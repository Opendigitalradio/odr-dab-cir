#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This is the main program that
# - runs rtl_sdr to record files containing samples
# - runs correlate_with_ref to calculate the CIR
# - runs a webserver to present the information
#
# Copyright (C) 2016
# Matthias P. Braendli, matthias.braendli@mpb.li
# http://www.opendigitalradio.org
# Licence: The MIT License, see LICENCE file

import sys
from bottle import route, run, template, static_file, request
import subprocess
import time
import multiprocessing as mp
import correlate_with_ref
import shlex
import argparse

# The record and correlate tasks run in alternance.
# Maybe later we want to run them simultaneously in a small
# pipeline.

class RTLSDR_CIR_Runner(mp.Process):
    def __init__(self, rtl_sdr_cmdline, iq_format, iq_file, fig_file):
        """Initialise a new runner, which runs rtl_sdr_cmdline
        that has to save to iq_file, and run the CIR analysis
        that will save to fig_file"""
        mp.Process.__init__(self)

        self.events = mp.Queue()
        self.rtl_sdr_cmdline = rtl_sdr_cmdline
        self.iq_format = iq_format
        self.iq_file = iq_file
        self.fig_file = fig_file

    def stop(self):
        self.events.put("quit")

    def run(self):
        while True:
            time.sleep(1)
            self.do_one_cir_run()

            try:
                ev = self.events.get_nowait()
                if ev == "quit":
                    break
            except mp.queues.Empty:
                pass

    def do_one_cir_run(self):
        rtlsdr = subprocess.Popen(self.rtl_sdr_cmdline)
        rtlsdr.wait()

        # The RTLSDR outputs u8 format
        cir_corr = correlate_with_ref.CIR_Correlate(self.iq_file, self.iq_format)
        cir_corr.plot(self.fig_file)

@route('/')
def index():
    return template('index',
            rtl_sdr_cmdline = rtl_sdr_cmdline,
            fig_file = FIG_FILE)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./static')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DAB Channel Impulse Measurement for RTL-SDR')

    # Options for the webserver
    parser.add_argument('--host', default='127.0.0.1', help='socket host (default: 127.0.0.1)',required=False)
    parser.add_argument('--port', default='8000', help='socket port (default: 8000)',required=False)
    parser.add_argument('--mhost', default='127.0.0.1', help='mux host (default: 127.0.0.1)',required=False)
    parser.add_argument('--mport', default='12720', help='mux port (default: 12720)',required=False)

    # Options for RTLSDR reception
    parser.add_argument('--freq', help='Receive frequency', required=True)
    parser.add_argument('--samps',
            default=10*196608,
            help='Number of samples to analyse in one run, one transmission frame at 2048000 samples per second is 196608 samples',
            required=False)

    parser.add_argument('--rate', default='2048000', help='Samplerate for RTLSDR receiver (2048000)', required=False)

    cli_args = parser.parse_args()

    # File to save the recorded IQ file to
    IQ_FILE = "static/rtlsdr.iq"
    IQ_FORMAT = "fc64"

    # The figures are saved to a file
    FIG_FILE = "static/rtlsdr.svg"

    # Build the rtl_sdr command line from the settings in config
    rtl_sdr_cmdline = shlex.split("rtl_sdr -f {} -n {} -s {} {}".format(
        cli_args.freq, cli_args.samps, cli_args.rate, IQ_FILE))

    rtl_sdr_cmdline = shlex.split("cp -v /home/bram/dab/autocorr/limus-zh2.100.14.25.trunc.iq {}".format(
        IQ_FILE))

    rtlsdr_cir = RTLSDR_CIR_Runner(rtl_sdr_cmdline, IQ_FORMAT, IQ_FILE, FIG_FILE)
    rtlsdr_cir.start()

    try:
        run(host=cli_args.host, port=int(cli_args.port), debug=True, reloader=False)
    finally:
        rtlsdr_cir.stop()
        rtlsdr_cir.join()
