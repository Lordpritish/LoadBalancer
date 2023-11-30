import matplotlib.pyplot as plt
import numpy as np
import sys
from copy import deepcopy

def construct_lists_from_file(f):
    server_to_in_requests = {}
    server_to_out_requests = {}

    while (f):
        line = f.readline().split()
        if (line == []):
            break
        server, time, direction = line

        if direction == "in":
            if server in server_to_in_requests:
                server_to_in_requests[server].append(float(time)*1000)
            else:
                server_to_in_requests[server] = [0, float(time)*1000]
                server_to_out_requests[server] = [0]
        elif direction == "out":
            if server in server_to_out_requests:
                server_to_out_requests[server].append(float(time)*1000)
            else:
                server_to_out_requests[server] = [0, float(time)*1000]
                server_to_in_requests[server] = [0]
        
        lastTime = float(time)*1000
    

    return server_to_in_requests, server_to_out_requests, lastTime

def plot_req_count(server_to_in_requests, lastTime):
    for server in server_to_in_requests:
        x = server_to_in_requests[server]
        y = list(range(len(x)))
        if x[-1] != lastTime:
            x.append(lastTime)
            y.append(y[-1])
        plt.plot(x, y, label = server, alpha=0.6)

    plt.xlabel("time (ms)")
    plt.ylabel("number of requests sent through load balancer")
    plt.legend()
    plt.savefig("total_req_count.png")
    plt.clf()

def plot_net_req_count(server_to_in_requests, server_to_out_requests, lastTime):
    for server in server_to_in_requests:
        x = sorted(server_to_in_requests[server] + server_to_out_requests[server])[1:]
        y = []
        for i in range(0, len(x)):
            t = x[i]
            if (t == 0):
                y.append(0)
            #append the count if it's incoming and decrement for outgoing requests
            elif t in server_to_in_requests[server]:
                y.append(y[-1] + 1)
            else:
                y.append(y[-1] - 1)

        if x[-1] != lastTime:
            x.append(lastTime)
            y.append(y[-1])
        plt.plot(x, y, label = server, alpha = 0.6)
    plt.xlabel("time (ms)")
    plt.ylabel("number of active connection")
    plt.legend()
    plt.savefig("active_connection.png")

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        std.error("Please enter the log text file")
    
    f = open(sys.argv[1], "r")
    server_to_in_requests, server_to_out_requests, lastTime = construct_lists_from_file(f)
    f.close()
    plot_req_count(deepcopy(server_to_in_requests), lastTime)
    plot_net_req_count(deepcopy(server_to_in_requests), deepcopy(server_to_out_requests), lastTime)
