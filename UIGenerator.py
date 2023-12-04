import matplotlib.pyplot as plt
import numpy as np
import sys
from copy import deepcopy

def construct_lists_from_file(f):
    server_to_start_connection = {}
    server_to_done_connection = {}

   
    if f:
        line = f.readline()
        servers = line.strip().split()  # get all servers assuming are space-separate
        lastTime = 0
        server_to_start_connection = {server: [] for server in servers}
        server_to_done_connection = {server: [] for server in servers}

        while (f):
            line = f.readline().split()
            if (line == []):
                break
            server, time, direction = line


            if direction == "start":
                server_to_start_connection[server].append(float(time)*1000)
            elif direction == "done":
                server_to_done_connection[server].append(float(time)*1000)
            
            lastTime = float(time)*1000

        return server_to_start_connection, server_to_done_connection, lastTime 
    else:
        exit()
    # initialixe the dict 





def server_to_num_request(server_to_start_connection):
    # Extracting data for plotting
    servers = list(server_to_start_connection.keys())
    num_requests = list(server_to_start_connection.values())

    # Number of requests for each server is the length of its response times
    num_requests_per_server = [len(response_times) for response_times in num_requests]

    # Creating a bar graph
    plt.bar(servers, num_requests_per_server, color='blue')
    plt.xlabel('Server')
    plt.ylabel('Number of Requests')
    plt.title('Number of Requests per Server')
    plt.legend()
    plt.savefig("num_req_per_server.png")
    plt.clf()


def plot_req_over_time_count(server_to_start_connection, lastTime):
    for server in sorted(server_to_start_connection):
        x = [0] + server_to_start_connection[server]
        y = list(range(len(x)))
        if x[-1] != lastTime:
            x.append(lastTime)
            y.append(y[-1])
        plt.plot(x, y, label = server, alpha=0.6)

    plt.xlabel("time (ms)")
    plt.ylabel("# of requests sent to Server over time")
    plt.savefig("req_sent_over_time.png")
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
    plt.savefig("active_connection.png")
    plt.clf()

def plot_average_response_time(server_to_start_connection, server_to_done_connection):
    x = []
    y = []

    for server in sorted(server_to_start_connection):
        if  len(server_to_start_connection[server]) != 0:
            average = (sum(server_to_done_connection[server]) - sum(server_to_start_connection[server])) / len(server_to_start_connection[server])
            x.append(server)
            y.append(average)
    #  This mean is a servr has large connection time its is slower
    plt.bar(x, y, width = 0.3)
    plt.xlabel("server")
    plt.ylabel("Average Response time (ms)")
    plt.savefig("average_response_time.png")
    plt.clf()

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        std.error("Please enter the log text file")

    f = open(sys.argv[1], "r")
    server_to_start_connection, server_to_done_connection, lastTime = construct_lists_from_file(f)
    f.close()
    fig = plt.figure(figsize= (10, 5))
    server_to_num_request(server_to_start_connection)
    plot_req_over_time_count(deepcopy(server_to_start_connection), lastTime)
    plot_net_req_count(deepcopy(server_to_start_connection), deepcopy(server_to_done_connection), lastTime)
    plot_average_response_time(deepcopy(server_to_start_connection), deepcopy(server_to_done_connection))
