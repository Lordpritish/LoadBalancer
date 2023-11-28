import random

class LoadBalancer:
    def __init__(self):
        self.live_servers = [] # [IP]
        self.number_of_servers = 0

    def get_next_server(self):
        pass

    def add_server(self, server,response_time):
        self.live_servers.append(server)
        self.number_of_servers += 1

    def delete_server(self, server):
        pass

    def update_response_time(self, server, new_response_time):
        pass
    
    def increment_connections(self, server):
        pass
    
    def decrement_connections(self, server):
        pass

    def get_server(self, server):
        # Add logic to get a server from the list
        if server in self.live_servers:
            return server
        return None

    def list_servers(self):
        # Add logic to return a list of live servers
        pass

class LeastResponseTimeBalancer(LoadBalancer):
    """"
    Algorithmic explanation:
        1. Find the server/s with the lowest active connections.
        2. If there are multiple servers with the lowest active connections, find the server/s with the shortest average response time. Following are some of the cases to note:
            Case1: If there are multiple servers with the same shortest average response time, then apply the round-robin method and assign the new request to the server that has its turn.
            Case2: If the server is exactly one, assign the new request to this server.
        3. If the server is exactly one, assign the new request to this server.
    """

    def __init__(self):
        super().__init__()
        self.active_connections = {} # server_ip -> # of connections
        self.response_times = {} # IP -> response_time
        self.round_robin_counter = 0


    def add_server(self, server,response_time):
        self.live_servers.append(server)
        self.response_times[server] = response_time  
        self.active_connections[server] = 0
        self.number_of_servers += 1

    def delete_server(self, server):
        if server in self.live_servers:
            self.live_servers.remove(server)
            del self.active_connections[server]
            del self.response_times[server]
    
    def update_response_time(self, server, new_response_time):
        # Manually update the response time for a server
        self.response_times[server] = new_response_time
    
    def increment_connections(self, server):
        # Increment the number of active connections for a server
        self.active_connections[server] += 1
    
    def decrement_connections(self, server):
        # Decrement the number of active connections for a server
        self.active_connections[server] -= 1
        if self.active_connections[server] < 0:
            self.active_connections[server] = 0

    def get_next_server(self):
        # Find servers with the lowest active connections
        min_active_connections = min(list(self.active_connections.values()))
        lowest_active_servers = [server for server, connections in self.active_connections.items() if connections == min_active_connections]

        # If there are multiple servers with the lowest active connections, find the one with the shortest average response time
        if len(lowest_active_servers) > 1:
            min_response_time = min(self.response_times[server] for server in lowest_active_servers)
            lowest_response_time_servers = [server for server in lowest_active_servers if self.response_times[server] == min_response_time]

            # If there are still multiple servers, use round-robin
            if len(lowest_response_time_servers) > 1:
                chosen_server = lowest_response_time_servers[self.round_robin_counter % len(lowest_response_time_servers)]
                self.round_robin_counter += 1
            else:
                chosen_server = lowest_response_time_servers[0]
        else:
            chosen_server = lowest_active_servers[0]

        # Update active connections and return the chosen server
        self.active_connections[chosen_server] += 1
        return chosen_server
    


class RandomBalancer(LoadBalancer):

    def get_next_server(self):
        if self.number_of_servers == 0:
            return None
        return random.choice(self.live_servers)

    def delete_server(self, server):
        # Add logic to delete a server from the list
        if server in self.live_servers:
            self.live_servers.remove(server)
            self.number_of_servers -= 1


class RoundRobinBalancer(LoadBalancer):
    def __init__(self):
        super().__init__()
        self.current_server_index = 0

    def get_next_server(self):
        if self.number_of_servers == 0:
            raise None
        
        next_server = self.live_servers[self.current_server_index]
        self.current_server_index = (self.current_server_index + 1) % self.number_of_servers
        return next_server

      
    def delete_server(self, server):
        # Add logic to delete a server from the list
        if server in self.live_servers:
            self.live_servers.remove(server)
            self.number_of_servers -= 1
            self.current_server_index %= max(1, self.number_of_servers)


class WeightedRoundRobinBalancer(RoundRobinBalancer):
    def __init__(self, weights):
        super().__init__()
        self.weights = weights.copy() # ip -> weights
        self.curr_weights = weights # ip -> weights
    
    def get_next_server(self):
        if self.number_of_servers == 0:
            return None

        if sum(list(self.curr_weights.values())) == 0:
            self.curr_weights = self.weights.copy()
        while True:
   
            current_server = self.live_servers[self.current_server_index]
            current_weight = self.curr_weights[current_server]

            if current_weight > 0:
                self.current_server_index = (self.current_server_index + 1) % self.number_of_servers
                self.curr_weights[current_server] -= 1
                return current_server
            

            self.current_server_index = (self.current_server_index + 1) % self.number_of_servers



