import matplotlib.pyplot as plt
import numpy as np
import sys
from copy import deepcopy

def construct_lists_from_file(f):
    server_to_start_connection = {}
    server_to_done_connection = {}

    lastTime = 0
    while (f):
        line = f.readline().split()
        if (line == []):
            break
        server, time, direction = line

        if direction == "start":
            if server in server_to_start_connection:
                server_to_start_connection[server].append(float(time)*1000)
            else:
                server_to_start_connection[server] = [float(time)*1000]
                server_to_done_connection[server] = []
        elif direction == "done":
            if server in server_to_done_connection:
                server_to_done_connection[server].append(float(time)*1000)
            else:
                server_to_done_connection[server] = [float(time)*1000]
                server_to_start_connection[server] = []
        
        lastTime = float(time)*1000
    

    return server_to_start_connection, server_to_done_connection, lastTime

def plot_req_count(server_to_start_connection, lastTime):
    for server in sorted(server_to_start_connection):
        x = [0] + server_to_start_connection[server]
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

def plot_net_req_count(server_to_start_connection, server_to_done_connection, lastTime):
    for server in sorted(server_to_start_connection):
        sortedT = sorted(server_to_start_connection[server] + server_to_done_connection[server])
        x = [0]
        y = [0]
        for i in range(0, len(sortedT)):
            t = sortedT[i]
            lastVal = y[-1]
            #append the count if it's incoming and decrement for outgoing requests
            if t in server_to_start_connection[server]:
                x = x + [t, t]
                y.append(lastVal)
                y.append(lastVal + 1)
            else:
                x = x + [t, t]
                y.append(lastVal)
                y.append(lastVal - 1)

        if x[-1] != lastTime:
            x.append(lastTime)
            y.append(y[-1])
        plt.plot(x, y, label = server, alpha = 0.6, linewidth=1)
    plt.xlabel("time (ms)")
    plt.ylabel("number of active connection")
    plt.legend()
    plt.savefig("active_connection.png")
    plt.clf()

def plot_average_connection_time(server_to_start_connection, server_to_done_connection):
    x = []
    y = []
    for server in sorted(server_to_start_connection):
        average = (sum(server_to_done_connection[server]) - sum(server_to_start_connection[server])) / len(server_to_start_connection[server])
        x.append(server)
        y.append(average)
    
    plt.bar(x, y, width = 0.3)
    plt.xlabel("server")
    plt.ylabel("average connection time (ms)")
    plt.legend(fontsize="x-large")
    plt.savefig("average_connection_time.png")
    plt.clf()

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        std.error("Please enter the log text file")
    
    f = open(sys.argv[1], "r")
    server_to_start_connection, server_to_done_connection, lastTime = construct_lists_from_file(f)
    f.close()
    fig = plt.figure(figsize= (10, 5))
    plot_req_count(deepcopy(server_to_start_connection), lastTime)
    plot_net_req_count(deepcopy(server_to_start_connection), deepcopy(server_to_done_connection), lastTime)
    plot_average_connection_time(deepcopy(server_to_start_connection), deepcopy(server_to_done_connection))