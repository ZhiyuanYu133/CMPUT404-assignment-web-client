#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

# Parse the url of GET request
def parse_url(url, args=None):
    # Use urllib.parse to parse this url
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.netloc
    path = parsed_url.path
    queries = parsed_url.query

    # set request params
    if len(queries) > 0 or (args is not None and len(args) > 0):
        path += '?'

    if len(queries) > 0 and args is not None and len(args) > 0:
        queries += '&'

    if isinstance(args, dict):
        queries += urllib.parse.urlencode(args)

    if len(queries) > 0:
        path += queries

    if len(path) == 0:
        path = '/'

    return host, path

# Get the GET request message
def get_get_request_message(host, path):
    return f'GET {path} HTTP/1.1\r\nHost: {host}\r\n' + \
            'Connection: close\r\n' + \
           f'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36\r\n\r\n'

# Get the POST request message
def get_post_request_message(host, path, args):
    params = ''
    if args is not None:
        params = urllib.parse.urlencode(args)

    return f'POST {path} HTTP/1.1\r\nHost: {host}\r\n' + \
           'Connection: close\r\n' + \
           'Content-Type: application/x-www-form-urlencoded\r\n' + \
        f'Content-Length: {len(params)}\r\n' + \
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36\r\n\r\n' + \
        params

# Read one line from the socket
def read_one_line(host_socket: socket):
    line = b''
    while True:
        byte = host_socket.recv(1)
        if byte == b'\r':
            host_socket.recv(1)
            break
        else:
            line += byte
    return line.decode('utf-8')

class HTTPClient(object):
    # Get the host port from the host address
    def get_host_port(self, host):
        split = host.split(':')
        port = 80
        if len(split) > 1:
            host = split[0]
            port = int(split[1])
        return host, port

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        # get the response code
        split = data.split('\r\n')[0].split()
        code = int(split[1])
        return code

    def get_headers(self,data):
        # Get the header of the response
        headers = {}
        for line in data.split('\r\n')[1:]:
            if len(line) == 0:
                break
            split = line.split(':')
            headers[split[0].strip()] = split[1].strip()

        return headers

    def get_body(self, data):
        # read the response body
        body = ''
        # Find the body of the data
        i = 0
        split = data.split('\r\n')
        for i in range(len(split)):
            if len(split[i]) == 0:
                break

        body = '\r\n'.join(split[i+1:])

        return body

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        code = 404
        body = ""

        # Parse the url
        host, path = parse_url(url, args)

        # Connect to the host
        host, port = self.get_host_port(host)
        try:
            self.connect(host, port)
        except Exception:
            return HTTPResponse(code, body)

        # Set the GET request message
        req_message = get_get_request_message(host, path)

        # Send the request message to the host
        self.sendall(req_message)

        # Retrieve the response
        data = self.recvall(self.socket)
        code = self.get_code(data)
        body = self.get_body(data)
        self.close()
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 404
        body = ""

        # Parse the url
        host, path = parse_url(url)

        # Connect to the host
        host, port = self.get_host_port(host)
        try:
            self.connect(host, port)
        except Exception:
            return HTTPResponse(code, body)

        # Set the POST request message
        req_message = get_post_request_message(host, path, args)

        # Send the request message to the host
        self.sendall(req_message)

        # Retrieve the response
        data = self.recvall(self.socket)
        code = self.get_code(data)
        body = self.get_body(data)
        self.close()
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )

if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
