#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Nick Groenen <nick@groenen.me>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
import os
import socket
import signal
import sys
import threading
import time

import speedtest_cli


def main():
    speedtest_cli.shutdown_event = threading.Event()

    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', default=10, type=int,
                        help='HTTP timeout in seconds. Default 10')
    parser.add_argument('--secure', action='store_true',
                        help='Use HTTPS instead of HTTP when communicating '
                             'with speedtest.net operated servers')
    parser.add_argument('--graphite-host', type=str, default='localhost',
                        help='The graphite host to publish results to')
    parser.add_argument('--graphite-port', type=int, default=2003,
                        help='The graphite (line-receiver) port to publish results to')
    parser.add_argument('--graphite-prefix', type=str, default="speedtest",
                        help='The graphite metrics prefix')
    args = parser.parse_args()

    socket.setdefaulttimeout(args.timeout)
    speedtest_cli.build_user_agent()

    if args.secure:
        speedtest_cli.scheme = 'https'

    try:
        config = speedtest_cli.getConfig()
    except speedtest_cli.URLError:
        print('Cannot retrieve speedtest configuration')
        sys.exit(1)

    servers = speedtest_cli.closestServers(config['client'])
    best = speedtest_cli.getBestServer(servers)

    print("Using speedtest.net server hosted by {sponsor} ({name}).\n"
          "Host: {host}\nDistance: {d:0.1f} km\nLatency: {latency} ms".format(**best))

    sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    urls = []
    for size in sizes:
        for i in range(0, 4):
            urls.append('%s/random%sx%s.jpg' %
                        (os.path.dirname(best['url']), size, size))
    dlspeed = speedtest_cli.downloadSpeed(urls, True)
    print('Download: %0.2f Mbit/s' % ((dlspeed / 1000 / 1000) * 8))

    sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
    sizes = []
    for size in sizesizes:
        for i in range(0, 25):
            sizes.append(size)
    ulspeed = speedtest_cli.uploadSpeed(best['url'], sizes, True)
    print('Upload: %0.2f Mbit/s' % ((ulspeed/ 1000 / 1000) * 8))

    t = int(time.time())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.graphite_host, args.graphite_port))
    s.send(
        "{prefix}.latency {latency} {timestamp}\n".format(
        prefix=args.graphite_prefix,
        latency=best['latency'],
        timestamp=t,
    ))
    s.send(
        "{prefix}.distance {distance} {timestamp}\n".format(
        prefix=args.graphite_prefix,
        distance=best['d'],
        timestamp=t,
    ))
    s.send(
        "{prefix}.upload {upload} {timestamp}\n".format(
        prefix=args.graphite_prefix,
        upload=ulspeed,
        timestamp=t,
    ))
    s.send(
        "{prefix}.download {download} {timestamp}\n".format(
        prefix=args.graphite_prefix,
        download=dlspeed,
        timestamp=t,
    ))
    s.close()


if __name__ == "__main__":
    main()
