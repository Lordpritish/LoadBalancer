import random

class StaticLoadBalancer:
    def __init__(self):
        self.live_servers = {} # IP -> MAC,port
        self.number_of_servers = 0

    def get_next_server(self):
        pass

    def add_server(self, server,hwsrc,port):
        self.live_servers[server] = hwsrc,port
        self.number_of_servers += 1

    def delete_server(self, server):
        # Add logic to delete a server from the list
        pass

    def get_server(self, server):
        # Add logic to delete a server from the list
        return self.live_servers.get(server, (None,None))

    def list_servers(self):
        # Add logic to return a list of live servers
        pass


class RandomBalancer(StaticLoadBalancer):

    def get_next_server(self):
        if self.number_of_servers == 0:
            return None
        return random.choice(list(self.live_servers.keys()))

    def delete_server(self, server):
        # Add logic to delete a server from the list
        if server in self.live_servers:
            del self.live_servers[server]
            self.number_of_servers -= 1


class RoundRobinBalancer(StaticLoadBalancer):
    def __init__(self):
        super().__init__()
        self.current_server_index = 0

    def get_next_server(self):
        if self.number_of_servers == 0:
            raise None
        
        next_server = list(self.live_servers.keys())[self.current_server_index]
        self.current_server_index = (self.current_server_index + 1) % self.number_of_servers
        return next_server

      
    def delete_server(self, server):
        # Add logic to delete a server from the list
        if server in self.live_servers:
            del self.live_servers[server]
            self.number_of_servers -= 1
            self.current_server_index %= max(1, self.number_of_servers)


class WeightedRoundRobinBalancer(RoundRobinBalancer):
    def __init__(self, weights):
        super().__init__()
        self.weights = weights # ip -> weights
        self.curr_weights = weights # ip -> weights
        

    
    def get_next_server(self):
        if self.number_of_servers == 0:
            return None
        # If all weights are zero, reset weights to their original values
        # print(type(self.curr_weights.values()))/
        if sum(self.curr_weights.values()) == 0:
            self.curr_weights = self.weights
        while True:
             
            current_server = list(self.live_servers.keys())[self.current_server_index]
            current_weight = self.curr_weights[current_server]

            if current_weight > 0:
                self.current_server_index = (self.current_server_index + 1) % self.number_of_servers
                self.curr_weights[current_server] -= 1
                return current_server

            self.current_server_index = (self.current_server_index + 1) % self.number_of_servers



