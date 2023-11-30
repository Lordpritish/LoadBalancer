from pox.core import core
from pox.lib.addresses import IPAddr, EthAddr
from FlowRule import FlowRuleManager
from ArpHandler import ARPHandler
from PingHandler import PingHandler
from LoadBalancingAlgthm import RandomBalancer,RoundRobinBalancer,WeightedRoundRobinBalancer,LoadBalancer, LeastResponseTimeBalancer
from RequestLogWriter import RequestLogWriter
import pox.openflow.libopenflow_01 as of
import time
import pox.lib.packet as pkt
from enum import Enum
from pox.lib.packet.icmp import icmp , TYPE_ECHO_REPLY

log = core.getLogger()
RANDOM = 1
ROUND_ROBIN = 2
WEIGHTED_ROUND_ROBIN = 3
LEAST_RESPONSE_TIME = 4


class ConnectionStatus(Enum):
    NEW_CONNECTION = "New connection started"
    CONNECTION_ENDED = "Connection ended"
    CONNECTION_IN_PROGRESS = "Connection in progress"

class SimpleLoadBalancer:
    def __init__(self, lb_ip,algthm:LoadBalancer ,servers=[]):
        core.openflow.addListeners(self)
        self.lb_ip = IPAddr(lb_ip)
        self.mac = EthAddr("0A:00:00:00:00:01")
        self.ethernet_broad = EthAddr("ff:ff:ff:ff:ff:ff")
        self.servers = [IPAddr(ip) for ip in servers]
        self.flow_manager = FlowRuleManager(None, self.mac, self.lb_ip)
        self.arp_handler = ARPHandler(self.mac, self.lb_ip, self.ethernet_broad)
        self.ping_handler = PingHandler(self.mac,self.lb_ip)
        self.server_mac_to_port = {} # {ip :  { mac: , port :}}
        self.client_table = {} 
        self.balancing_algorithm = algthm
        self.ping_probe_start_delay = 5
        
        
        self.outstanding_probes = {} # IP -> expire_time
        self.probe_cycle_time = 5 # How quickly do we probe ?
        self.ping_timeout = 2  # How long do we wait for an PING reply before we consider a server dead?
      
        self.connections_map = {} # client:port -> server_ip

        self.req_log_writer = RequestLogWriter(servers)

    def _do_expire (self):
        """
        Expire probes

        Each of these should only have a limited lifetime.
        """
        t = time.time()

        # Expire probes
        for ip,expire_at in list(self.outstanding_probes.items()):
            if t > expire_at:
                self.outstanding_probes.pop(ip, None)
                self.balancing_algorithm.delete_server(ip)
                log.warn("Server %s down", ip)

    def _do_ping_probe (self):
        """
        Send an ARP to a server to see if it's still up
        """
        self._do_expire()

        server = self.servers.pop(0)
        self.servers.append(server)
        
        self.ping_handler.send_ping_request(self.connection,server,self.server_mac_to_port[server]['mac'])

        self.outstanding_probes[server] = time.time() + self.ping_timeout


        core.callDelayed(self._probe_wait_time(), self._do_ping_probe)


    def _probe_wait_time (self):
        """
        Time to wait between probes
        """
        r = self.probe_cycle_time / float(len(self.servers))
        r = max(2.5, r) # Cap it at 1 per 2.5 second
        return r


    def _handle_ConnectionUp(self, event):
        self.connection = event.connection
        self.flow_manager.connection = event.connection
        for ip in self.servers:
            self.arp_handler.send_proxied_arp_request(self.connection, ip)
            log.info("SERVER ADDED")
        
        core.callDelayed(self.ping_probe_start_delay, self._do_ping_probe) 

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        if packet.type == packet.ARP_TYPE:
            # log.info("handle_arp_packet")
            self.handle_arp_packet(packet, event)
        elif packet.type == packet.IP_TYPE:
            log.info("handle_ip_packet")
            self.handle_ip_packet(packet, event)
        else:
            log.info("Unknown Packet type: %s" % packet.type)

    def handle_ping_packet(self,icmp_pkt,src_ip):
        if icmp_pkt.type == TYPE_ECHO_REPLY:
            if src_ip in self.outstanding_probes:
                # A server is (still?) up; cool.
                rtt  = (time.time() -  (self.outstanding_probes[src_ip] - self.ping_timeout)) * 1000 # convert into ms
                log.info("Round-trip time to %s: %.2f ms", src_ip, rtt)
                self.balancing_algorithm.update_response_time(src_ip,rtt)
 
                del self.outstanding_probes[src_ip]
                if not self.balancing_algorithm.get_server(src_ip):
                    self.balancing_algorithm.add_server(src_ip,rtt)
                    log.info("Server %s up", src_ip)

        

    def handle_arp_packet(self, packet, event):
        arpp = packet.payload
        packet_ip = arpp.protosrc
        
        if arpp.opcode == arpp.REPLY:
            log.info("ARP REPLY INCOMING for %s",packet_ip)

            if packet_ip not in self.server_mac_to_port:
                self.server_mac_to_port[packet_ip] = {'mac': EthAddr(arpp.hwsrc), 'port': event.port}
            return

        elif arpp.opcode == arpp.REQUEST:
            log.info("ARP REQUEST INCOMING")

            # Check if the ARP request's if its from from client then add it to clients table if not there already
            if packet_ip not in self.servers and packet_ip not in self.client_table:
                self.client_table[packet_ip] = {'mac': EthAddr(arpp.hwsrc), 'port': event.port}
                log.info("Added Client %s MAC to client_table" % (packet_ip))
                return
        
            # Send a proxied ARP reply if the ARP request is  from client -> load balancer's .
            if packet_ip in self.client_table.keys()  and  arpp.protodst == self.lb_ip:
                log.info("Client %s send ARP req to load balancer %s" % (packet_ip, arpp.protodst))
            # Handling server to client ARP requests.
            elif packet_ip in self.servers and arpp.protodst in self.client_table.keys():
                log.info("Server %s send ARP req to client %s" % (packet_ip, arpp.protodst))
            elif packet_ip in self.servers and arpp.protodst == self.lb_ip:
                log.info("Load Balancer %s send ARP req to server %s" % (self.lb_ip, packet_ip))

            self.arp_handler.send_proxied_arp_reply(packet, event.connection, event.port, self.mac)


    def handle_tcp_packet(self, packet,src_ip): 

        src_port = packet.srcport
        dst_port = packet.dstport

        # Assume HTTP server is running on port 80
        if dst_port == 80:
            if packet.SYN:
                # TCP SYN flag is set, indicating the start of the connection
                log.info("New connection from %s:%s has STARTED", src_ip, src_port)
                return  src_port,ConnectionStatus.NEW_CONNECTION
            elif packet.FIN or packet.RST:
                # TCP FIN flag is set, indicating the end of the connection
                log.info("Connection from %s:%s  ENDED", src_ip, src_port)
                return  src_port,ConnectionStatus.CONNECTION_ENDED
            else:
                log.info("Connection from %s:%s in PROGRESS , flag:%s", src_ip, src_port,packet.flags)
                return  src_port,ConnectionStatus.CONNECTION_IN_PROGRESS
        return None, None
    
    def _handle_new_connection(self, client_ip,client_port):
        server_ip = self.balancing_algorithm.get_next_server()
        if server_ip:
            self.balancing_algorithm.increment_connections(server_ip)
            self.connections_map[str(client_ip) + str(client_port)] = server_ip
            log.info("New connection from %s:%s to %s has started", client_ip,client_port,server_ip)

        return server_ip
    

    def _handle_connection_ended(self, client_ip,client_port):
        server_ip = self.connections_map.get(str(client_ip)  + str(client_port), None)
        if server_ip:
            self.balancing_algorithm.decrement_connections(server_ip)
            del self.connections_map[str(client_ip)  + str(client_port)]
            log.info(self.connections_map)
            log.info("Connection from %s:%s to %s has ENDED", client_ip,client_port,server_ip)
        return self.balancing_algorithm.get_server(server_ip)
    
    def _handle_connection_in_progress(self, client_ip,client_port):

        server_ip = self.connections_map.get(str(client_ip) + str(client_port), None)
        if server_ip:
            log.info("Connection from %s:%s  to %s is in progress", client_ip,client_port,server_ip)

        return self.balancing_algorithm.get_server(server_ip)

    def handle_ip_packet(self, packet, event):
        def drop():
            """
            Helper function to drop the packet.
            """
            if event.ofp.buffer_id is not None:
                # Kill the buffer
                msg = of.ofp_packet_out(data=event.ofp)
                self.connection.send(msg)
            return None

 
        ip_packet = packet.payload
        in_port = event.port

        src_ip = ip_packet.srcip
        dst_ip = ip_packet.dstip


        # Client to Server
        if src_ip not in self.servers and dst_ip == self.lb_ip:
            log.info("Client to Server")

            client_ip = src_ip
            server_ip = None
            if ip_packet.protocol == pkt.ipv4.TCP_PROTOCOL:
                tcp_packet = ip_packet.payload
                client_port,connection_status = self.handle_tcp_packet(tcp_packet,client_ip)
                if connection_status == ConnectionStatus.NEW_CONNECTION:
                    server_ip= self._handle_new_connection(client_ip,client_port)
                elif connection_status == ConnectionStatus.CONNECTION_ENDED:
                    server_ip = self._handle_connection_ended(client_ip,client_port)
                elif connection_status == ConnectionStatus.CONNECTION_IN_PROGRESS:
                    server_ip = self._handle_connection_in_progress(client_ip,client_port)
            
            
            if not server_ip:
                # Pick a server
                server_ip = self.balancing_algorithm.get_next_server()
                if not server_ip:
                    log.warn("No servers available!")
                    return drop()
            
            log.info("Server selected for client %s: %s" % (client_ip, server_ip))
            
            server_port = self.server_mac_to_port[server_ip]['port']
            server_mac = self.server_mac_to_port[server_ip]['mac']
            client_mac = self.client_table[client_ip]['mac']
    

            self.req_log_writer.write_request(str(server_ip), "in")
            
            log.info("send packet out %s  to  %s" % (client_ip, server_ip))
            self.flow_manager.send_packet_out(event.ofp.buffer_id, self.mac, server_mac, client_ip, server_ip, server_port, in_port, ip_packet)
            

        # Server to Client
        elif src_ip in self.servers and (dst_ip in self.client_table.keys()):
            log.info("Server to Client")
            server_ip , client_ip = src_ip,dst_ip

            client_mac = self.client_table[client_ip]['mac']
            client_port = self.client_table[client_ip]['port']

            self.req_log_writer.write_request(str(server_ip), "out")

            log.info("send packet out %s  to  %s" % (server_ip, client_ip))
            self.flow_manager.send_packet_out(event.ofp.buffer_id, self.mac, client_mac, self.lb_ip, client_ip, client_port, in_port, ip_packet)
        elif src_ip in self.servers and dst_ip == self.lb_ip and ip_packet.protocol == pkt.ipv4.ICMP_PROTOCOL:
            self.handle_ping_packet(ip_packet.payload,src_ip)
            


            

def launch(ip, servers,alg=RANDOM,weights=None):
    log.info("Loading Simple Load Balancer module")
    servers = servers.split(',')
    
    balancing_algorithm = None
    alg = int(alg)
    if alg == RANDOM:
        balancing_algorithm = RandomBalancer()
        # print(alg)
    elif alg == ROUND_ROBIN:
        balancing_algorithm = RoundRobinBalancer()
    elif alg == WEIGHTED_ROUND_ROBIN:
        if weights: 
            # assign weights
            weights = [int(weight) for weight in weights.split(',')]
            if len(servers) == len(weights):
                weights_dict = {IPAddr(server_ip): weight for server_ip, weight in zip(servers, weights)}
                balancing_algorithm = WeightedRoundRobinBalancer(weights_dict)
            else:
                log.error("Valid Weights must be provided for WEIGHTED_ROUND_ROBIN algorithm.")
                exit()  
        else:  
            log.error("Valid Weights must be provided for WEIGHTED_ROUND_ROBIN algorithm.")
            exit()  # Abort if weights are not provided
    elif alg == LEAST_RESPONSE_TIME:
        balancing_algorithm = LeastResponseTimeBalancer()

    core.registerNew(SimpleLoadBalancer, ip, balancing_algorithm,servers)
