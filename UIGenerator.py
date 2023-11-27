import matplotlib.pyplot as plt
import numpy as np
import sys


def construct_server_to_requests(f):
    server_to_requests = {}

    while (f):
        line = f.readline().split()
        if (line == []):
            break
        server, time = line
        if server in server_to_requests:
            server_to_requests[server].append(float(time))
        else:
            server_to_requests[server] = [0, float(time)]

    return server_to_requests

def plot_req_count(server_to_requests):
    for server in server_to_requests:
        x = server_to_requests[server]
        y = list(range(len(x)))
        plt.plot(x, y, label = server)
    plt.xlabel("time (seconds)")
    plt.ylabel("number of requests sent through load balancer")
    plt.legend()
    plt.savefig("log.png")

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        std.error("Please enter the log text file")
    
    f = open(sys.argv[1], "r")
    server_to_requests = construct_server_to_requests(f)
    f.close()
    plot_req_count(server_to_requests)