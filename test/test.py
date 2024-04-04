#!/usr/local/bin/env python3

# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import socket
import sys
import time

BYTES_ORDER = "little"

class TcpStreamClient:
    """Client"""
    def __init__(self, conn_tmo=5):
        self.conn_tmo = conn_tmo
        self.records = []

    def connect(self, endpoint):
        """Connect to the remote endpoint"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.conn_tmo)
        self.sock.connect(endpoint)

    def send_data(self, data):
        """Send data to a remote endpoint"""
        self.sock.sendall(data)
        self.recv_data()

    def recv_data(self):
        data = self.sock.recv(1024)
        curr = time.time_ns()
        delta = int(curr) - int.from_bytes(data, BYTES_ORDER)
        self.records.append(delta / 1000)

    def disconnect(self):
        """Close the client socket"""
        self.sock.close()
        assert(len(self.records) % 2)
        rec = sorted(self.records)
        print("For ", len(self.records), " samples, median = ", rec[int(len(rec)/2)])
        mean = sum(rec) / len(rec)
        res = sum((i - mean) ** 2 for i in rec) / len(rec)
        print("90th: ", rec[round((90/100)*(len(rec)))])
        print("95th: ", rec[round((95/100)*(len(rec)))])

def client_handler(args):
    client = TcpStreamClient()
    endpoint = (args.host, args.port)
    client.connect(endpoint)
    for i in range(10001):
        time.sleep(0.002)
        client.send_data(int(time.time_ns()).to_bytes(10, BYTES_ORDER))
    client.disconnect()


class TcpListener:
    """Server"""
    def __init__(self, conn_backlog=128):
        self.conn_backlog = conn_backlog

    def bind(self, port):
        """Bind and listen for connections on the specified port"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(self.conn_backlog)

    def recv_data(self):
        """Receive data from a remote endpoint"""
        while True:
            (from_client, _) = self.sock.accept()
            # Read 1024 bytes at a time
            while True:
                try:
                    data = from_client.recv(1024)
                    from_client.sendall(data)
                except socket.error:
                    break
                if not data:
                    break
            from_client.close()

def server_handler(args):
    server = TcpListener()
    server.bind(args.port)
    server.recv_data()


def main():
    parser = argparse.ArgumentParser(prog='tcp-sample')
    parser.add_argument("--version", action="version",
                        help="Prints version information.",
                        version='%(prog)s 0.1.0')
    subparsers = parser.add_subparsers(title="options")

    client_parser = subparsers.add_parser("client", description="Client",
                                          help="Connect to a given host and port.")
    client_parser.add_argument("host", type=str, help="The remote host address.")
    client_parser.add_argument("port", type=int, help="The remote port.")
    client_parser.set_defaults(func=client_handler)

    server_parser = subparsers.add_parser("server", description="Server",
                                          help="Listen on a given port.")
    server_parser.add_argument("port", type=int, help="The local port to listen on.")
    server_parser.set_defaults(func=server_handler)

    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
