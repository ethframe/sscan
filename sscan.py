#!/usr/bin/env python

import asyncore
import socket
from itertools import product
from collections import defaultdict


class ConnectScanner(asyncore.dispatcher):
    probes = {
        80: b"GET / HTTP/1.0\r\n\r\n",
        21: b"LIST\r\n",
        23: b"",
    }

    def __init__(self, targets, results):
        asyncore.dispatcher.__init__(self)
        self.targets, self.results = targets, results
        self.host, self.port = None, None
        self.fire()

    def fire(self):
        try:
            self.host, self.port = next(self.targets)
            self.probe = ConnectScanner.probes.get(self.port, None)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self.host, self.port))
        except StopIteration:
            pass

    def handle_connect(self):
        print("open: %s:%d" % (self.host, self.port))
        self.results[self.host][self.port]["open"] = True
        if self.probe is None:
            self.do_next()
        else:
            self.results[self.host][self.port]["probe"] = self.probe

    def handle_read(self):
        if self.probe is not None:
            reply = self.recv(128).decode("unicode_escape")
            print("reply: %s:%d\n\t%r" % (self.host, self.port, reply))
            self.results[self.host][self.port]["reply"] = reply
            self.do_next()

    def handle_write(self):
        if self.probe is not None:
            self.probe = self.probe[self.send(self.probe):]

    def do_next(self):
        self.close()
        self.fire()

    handle_close = handle_error = do_next


def scan(hosts, ports, parallelism=256):
    targets = product(hosts, ports)
    results = defaultdict(lambda: defaultdict(dict))
    scanners = [ConnectScanner(targets, results) for _ in range(parallelism)]
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
    return results


if __name__ == "__main__":
    scan(["127.0.0.1"], range(1, 1024), 256)
