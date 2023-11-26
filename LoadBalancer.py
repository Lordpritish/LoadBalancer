from pox.core import core
from pox.lib.addresses import IPAddr, EthAddr
from FlowRule import FlowRuleManager
from ArpHandler import ARPHandler
import pox.openflow.libopenflow_01 as of
import time
import random

log = core.getLogger()

class SimpleLoadBalancer:
    def __init__(self, service_ip, servers=[]):
        core.openflow.addListeners(self)
        self.service_ip = IPAddr(service_ip)
        self.mac = EthAddr("0A:00:00:00:00:01")
        self.ethernet_broad = EthAddr("ff:ff:ff:ff:ff:ff")
        self.servers = [IPAddr(ip) for ip in servers]
        self.flow_manager = FlowRuleManager(None, self.mac, self.service_ip)
        self.arp_handler = ARPHandler(self.mac, self.service_ip, self.ethernet_broad)
        self.server_mac_to_port = {}
        self.client_table = {}
        self.client_to_server_backup_map = {}


        self.outstanding_probes = {} # IP -> expire_time
        self.probe_cycle_time = 5 # How quickly do we probe?
        self.arp_timeout = 3 # How long do we wait for an ARP reply before we consider a server dead?
        self.live_servers = {} # IP -> MAC,port

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
                if ip in self.live_servers:
                    log.warn("Server %s down", ip)
                    del self.live_servers[ip]

    def _do_probe (self):
        """
        Send an ARP to a server to see if it's still up
        """
        self._do_expire()

        server = self.servers.pop(0)
        self.servers.append(server)

        
        self.arp_handler.send_proxied_arp_request(self.connection, server)

        self.outstanding_probes[server] = time.time() + self.arp_timeout

        core.callDelayed(self._probe_wait_time(), self._do_probe)

    def _probe_wait_time (self):
        """
        Time to wait between probes
        """
        r = self.probe_cycle_time / float(len(self.servers))
        r = max(.25, r) # Cap it at four per second
        return r

    def _pick_server (self):
        """
        Pick a server for a (hopefully) new connection
        """
        return random.choice(list(self.live_servers.keys()))

    def _handle_ConnectionUp(self, event):
        self.connection = event.connection
        self.flow_manager.connection = event.connection
        for ip in self.servers:
            self.arp_handler.send_proxied_arp_request(self.connection, ip)
            log.info("SERVER ADDED")
        self._do_probe()

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

    def handle_arp_packet(self, packet, event):
        arpp = packet.payload
        packet_ip = arpp.protosrc
        
        if arpp.opcode == arpp.REPLY:
            # log.info("here")
            # Check if the ARP reply's source IP is not known as a server, then add it.
            if packet_ip in self.outstanding_probes:
                # A server is (still?) up; cool.
                del self.outstanding_probes[packet_ip]
                if (self.live_servers.get(packet_ip, (None,None))
                    == (arpp.hwsrc,event.port)):
                # Ah, nothing new here.
                    pass
                else:
                    # Ooh, new server.
                    self.live_servers[packet_ip] = arpp.hwsrc,event.port
                    log.info("Server %s up", packet_ip)

            if packet_ip not in self.server_mac_to_port:
                self.server_mac_to_port[packet_ip] = {'mac': EthAddr(arpp.hwsrc), 'port': event.port}

        elif arpp.opcode == arpp.REQUEST:
            log.info("ARP REQUEST INCOMING")
            # Check if the ARP request's source IP is not known as a server or a client, then add it to clients.
            if packet_ip not in self.server_mac_to_port and packet_ip not in self.client_table:
                self.client_table[packet_ip] = {'mac': EthAddr(arpp.hwsrc), 'port': event.port}
                log.info("Added Client %s MAC to client_table" % (packet_ip))
        
            # Send a proxied ARP reply if the ARP request is for the load balancer's IP.
            if packet_ip in self.client_table.keys()  and  arpp.protodst == self.service_ip:
                log.info("Client %s send ARP req to load balancer %s" % (packet_ip, arpp.protodst))
                self.arp_handler.send_proxied_arp_reply(packet, event.connection, event.port, self.mac)

            # Handling server to client ARP requests.
            elif packet_ip in self.server_mac_to_port.keys() and arpp.protodst in self.client_table.keys():
                log.info("Server %s send ARP req to client %s" % (packet_ip, arpp.protodst))
                self.arp_handler.send_proxied_arp_reply(packet, event.connection, event.port, self.mac)

            else:
                log.info("Invalid ARP req")

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

        # Client to Server
        if ip_packet.srcip not in self.servers and ip_packet.dstip == self.service_ip:
            log.info("Client to Server")

            client_ip = ip_packet.srcip

            if len(self.live_servers) == 0:
                self.log.warn("No servers available!")
                return drop()

            # Pick a server
            server_ip = self._pick_server()
            log.info("Server selected for client %s: %s" % (client_ip, server_ip))
            
            # Update mapping for backup
            self.client_to_server_backup_map[client_ip] = server_ip

            server_port = self.server_mac_to_port[server_ip]['port']
            server_mac = self.server_mac_to_port[server_ip]['mac']
            client_mac = self.client_table[client_ip]['mac']
            self.flow_manager.install_client_to_server(server_port, client_ip, server_ip, server_mac)
            self.flow_manager.install_server_to_client(in_port, server_ip, client_ip, client_mac)

            log.info("send packet out %s  to  %s" % (client_ip, server_ip))
            self.flow_manager.send_packet_out(event.ofp.buffer_id, self.mac, server_mac, client_ip, server_ip, server_port, in_port, packet.next)
            

        # Server to Client
        elif ip_packet.srcip in self.servers and (ip_packet.dstip in self.client_table.keys()):
            log.info("Server to Client")
            server_ip = ip_packet.srcip

            # Find corresponding client IP from backup mapping
            client_ip = next((cip for cip, sip in self.client_to_server_backup_map.items() if sip == server_ip), None)
            
            if client_ip:
                client_mac = self.client_table[client_ip]['mac']
                client_port = self.client_table[client_ip]['port']
                self.flow_manager.install_server_to_client(client_port, server_ip, client_ip, client_mac)

                log.info("send packet out %s  to  %s" % (self.service_ip, client_ip))
                self.flow_manager.send_packet_out(event.ofp.buffer_id, self.mac, self.client_to_server_backup_map[server_ip]['mac'], self.service_ip, client_ip, client_port, in_port, packet.next)
            else:
                log.error("Mapping missing. Server IP: %s", server_ip)

def launch(ip, servers):
    log.info("Loading Simple Load Balancer module")
    servers = servers.split(',')
    core.registerNew(SimpleLoadBalancer, ip, servers)