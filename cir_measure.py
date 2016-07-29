#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This is the main program that
# - runs rtl_tcp to record files containing samples
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
import datetime
import multiprocessing as mp
import threading
import socket
import correlate_with_ref
import shlex
import argparse
import collections
import numpy as np

# The record and correlate tasks run in alternance.
# Maybe later we want to run them simultaneously in a small
# pipeline.

class RTLSDR_Receiver(threading.Thread):
    """Connection between the rtlsdr and our script is done using a TCP socket. This
    class handles running the rtl_tcp tool, and reads the incoming data stream into
    a local buffer. The buffer size is capped, and works as a FIFO, because analysis
    of the data is slower than capturing it. We therefore want to lose some data"""

    def __init__(self, options):
        threading.Thread.__init__(self)

        self.freq = float(options.freq)
        self.rate = int(options.rate)
        self.samps = int(options.samps)
        self.gain = float(options.gain)

        # We want to keep twice the amount of samples
        # in the queue to have some margin. Samples are
        # two bytes because they are I/Q interleaved u8
        self.max_num_bytes = self.samps * 2 * 2

        self.event_stop = threading.Event()

        self.rtl_tcp_port = 59152 # chosen randomly

        self.data_queue = collections.deque()

        # While the data_queue is itself thread-safe, we need to make sure
        # the consumer cannot preeempt the little housekeeping we do in run()
        # to keep the maximum queue length.
        self.data_lock = threading.Lock()

        self.rtlsdr_proc = None

    def run(self):
        rtl_tcp_cmdline = shlex.split("rtl_tcp -f {} -s {} -g {} -p {}".format(self.freq, self.rate, self.gain, self.rtl_tcp_port))
        self.rtlsdr_proc = subprocess.Popen(rtl_tcp_cmdline)

        time.sleep(1.5)

        self.sock = socket.socket()
        self.sock.connect(("localhost", self.rtl_tcp_port))

        while not self.event_stop.is_set():
            try:
                samples = self.sock.recv(1024)

                self.data_queue.extend(samples)
            except:
                print('Socket error')
                break

            self.data_lock.acquire()

            # try/catch/except to make sure we release the lock, and
            # re-raise any exception up
            try:
                n_bytes = len(self.data_queue)

                if n_bytes > self.max_num_bytes:
                    num_to_delete = n_bytes - self.max_num_bytes
                    for i in range(num_to_delete):
                        self.data_queue.popleft()
            except:
                raise
            finally:
                self.data_lock.release()
        print("Receiver leaving")

        self.sock.close()

        self.rtlsdr_proc.terminate()

        self.rtlsdr_proc.wait()

        print("Receiver thread ends")

    def stop(self):
        self.event_stop.set()
        self.join()

    def get_samples(self, num_samples):
        """Return a string containing num_bytes if that is available,
        or return None if not enough data available"""
        ret = None

        num_bytes = num_samples * 2

        self.data_lock.acquire()

        try:
            n_bytes = len(self.data_queue)

            if n_bytes > num_bytes:
                ret = "".join(
                        self.data_queue.popleft()
                        for i in range(num_bytes))
        except:
            raise
        finally:
            self.data_lock.release()

        return ret


class RTLSDR_CIR_Runner(mp.Process):
    def __init__(self, options, iq_file, fig_file):
        """Initialise a new runner, which runs rtl_tcp
        that will save to iq_file, and run the CIR analysis
        that will save to fig_file.

        options must contain freq, rate and samps fields"""
        mp.Process.__init__(self)

        self.freq = float(options.freq)
        self.samps = int(options.samps)

        self.receiver = RTLSDR_Receiver(options)

        self.events = mp.Queue()

        self.iq_file = iq_file
        self.fig_file = fig_file

    def stop(self):
        self.events.put("quit")
        self.join()

    def run(self):

        self.receiver.start()

        while True:
            time.sleep(1)
            try:
                samps = self.receiver.get_samples(self.samps)
                if samps:
                    print("Got {} samples".format(len(samps)))
                    # The RTLSDR outputs u8 format
                    iq_data = np.array( [ord(c) for c in samps], np.uint8 )
                    self.do_one_cir_run(iq_data)
                else:
                    print("Got 0 samples")

            except Exception as e:
                print("Exception occurred: {}".format(e))
            except KeyboardInterrupt:
                print("Keyhoard Interrupt")
                break

            try:
                ev = self.events.get_nowait()
                if ev == "quit":
                    break
            except mp.queues.Empty:
                pass

        self.receiver.stop()

    def do_one_cir_run(self, iq_data):
        print("Starting correlation")
        cir_corr = correlate_with_ref.CIR_Correlate(iq_data=iq_data, iq_format="u8")

        title = "Correlation on {}kHz done at {}".format(
                int(self.freq / 1000),
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        cir_corr.plot(self.fig_file, title)

@route('/')
def index():
    return template('index',
            freq = cli_args.freq,
            rate = cli_args.rate,
            gain = cli_args.gain,
            fig_file = FIG_FILE)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./static')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DAB Channel Impulse Measurement for RTL-SDR')

    # Options for the webserver
    parser.add_argument('--host', default='127.0.0.1', help='socket host (default: 127.0.0.1)',required=False)
    parser.add_argument('--port', default='8000', help='socket port (default: 8000)',required=False)

    # Options for RTLSDR reception
    parser.add_argument('--freq', help='Receive frequency', required=True)
    parser.add_argument('--samps',
            default=10*196608,
            help='Number of samples to analyse in one run, one transmission frame at 2048000 samples per second is 196608 samples',
            required=False)
    parser.add_argument('--gain', default=20, help='Gain setting for rtl_sdr', required=False)

    parser.add_argument('--rate', default='2048000', help='Samplerate for RTLSDR receiver (2048000)', required=False)

    cli_args = parser.parse_args()

    # File to save the recorded IQ file to
    IQ_FILE = "static/rtlsdr.iq"

    # The figures are saved to a file
    FIG_FILE = "static/rtlsdr.svg"

    rtlsdr_cir = RTLSDR_CIR_Runner(cli_args, IQ_FILE, FIG_FILE)
    rtlsdr_cir.start()

    try:
        run(host=cli_args.host, port=int(cli_args.port), debug=True, reloader=False)
    finally:
        rtlsdr_cir.stop()
