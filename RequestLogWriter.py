from pox.lib.packet.arp import arp
from pox.core import core
from pox.lib.packet.ethernet import ethernet
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
import time
import matplotlib.pyplot as plt
import numpy as np
import sys

log = core.getLogger()

class RequestLogWriter:
    def __init__(self, servers):
        self.start_time = None
        self.first_req_processed = False
        self.f = open("req_count.txt", "w")
    
    def write_request(self, server):
        if not self.first_req_processed: 
            self.first_req_processed = True
            self.start_time = time.time()
        self.f.write(server + " " + str(time.time() - self.start_time) + "\n")
        