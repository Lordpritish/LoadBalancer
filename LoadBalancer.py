from pox.core import core
from pox.lib.addresses import IPAddr, EthAddr
from FlowRule import FlowRuleManager
from ArpHandler import ARPHandler
import random

log = core.getLogger()


class SimpleLoadBalancer:
    def __init__(self, service_ip, server_ips=[]):
        core.openflow.addListeners(self)
        self.service_ip = IPAddr(service_ip)
        self.lb_mac = EthAddr("0A:00:00:00:00:01")
        self.ethernet_broad = EthAddr("ff:ff:ff:ff:ff:ff")
        self.server_ips = [IPAddr(ip) for ip in server_ips]
        self.flow_manager = FlowRuleManager(None, self.lb_mac, self.service_ip)
        self.arp_handler = ARPHandler(self.lb_mac, self.service_ip, self.ethernet_broad)
        self.mac_to_port = {}
        self.client_table = {}
        self.lb_map = {}

    def _handle_ConnectionUp(self, event):
        self.connection = event.connection
        self.flow_manager.connection = event.connection
        for ip in self.server_ips:
            self.arp_handler.send_proxied_arp_request(self.connection, ip)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        if packet.type == packet.ARP_TYPE:
            self.handle_arp_packet(packet, event)
        elif packet.type == packet.IP_TYPE:
            self.handle_ip_packet(packet, event)
        else:
            log.info("Unknown Packet type: %s" % packet.type)

    def handle_arp_packet(self, packet, event):
        arp_packet = packet.payload
        if arp_packet.opcode == arp_packet.REPLY:
            # Check if the ARP reply's source IP is not known as a server, then add it.
            if arp_packet.protosrc not in self.mac_to_port:
                self.mac_to_port[arp_packet.protosrc] = {'server_mac': EthAddr(arp_packet.hwsrc), 'port': event.port}

        elif arp_packet.opcode == arp_packet.REQUEST:
            # Check if the ARP request's source IP is not known as a server or a client, then add it to clients.
            if arp_packet.protosrc not in self.mac_to_port and arp_packet.protosrc not in self.client_table:
                self.client_table[arp_packet.protosrc] = {'client_mac': EthAddr(arp_packet.hwsrc), 'port': event.port}

            # Send a proxied ARP reply if the ARP request is for the load balancer's IP.
            if arp_packet.protodst == self.service_ip:
                log.info("Client %s send ARP req to load balancer %s" % (arp_packet.protosrc, arp_packet.protodst))
                self.arp_handler.send_proxied_arp_reply(packet, event.connection, event.port, self.lb_mac)

            # Handling server to client ARP requests.
            elif arp_packet.protosrc in self.mac_to_port and arp_packet.protodst in self.client_table:
                log.info("Server %s send ARP req to client %s" % (arp_packet.protosrc, arp_packet.protodst))
                self.arp_handler.send_proxied_arp_reply(packet, event.connection, event.port, self.lb_mac)

            else:
                log.info("Invalid ARP req")

    def handle_ip_packet(self, packet, event):
        ip_packet = packet.payload
        if ip_packet.dstip == self.service_ip:  # Client to Server
            client_ip = ip_packet.srcip
            self.update_lb_mapping(client_ip)
            server_ip = self.lb_map.get(client_ip)
            if server_ip:
                outport = self.mac_to_port[server_ip]['port']
                server_mac = self.mac_to_port[server_ip]['server_mac']
                self.flow_manager.install_client_to_server(outport, client_ip, server_ip, server_mac)
        elif ip_packet.srcip in [server_ip for server_ip in self.server_ips]:  # Server to Client
            server_ip = ip_packet.srcip
            client_ip = next((cip for cip, sip in self.lb_map.items() if sip == server_ip), None)
            if client_ip:
                client_mac = self.client_table[client_ip]['client_mac']
                outport = self.client_table[client_ip]['port']
                self.flow_manager.install_server_to_client(outport, server_ip, client_ip, client_mac)

    def update_lb_mapping(self, client_ip):
        if client_ip not in self.lb_map:
            available_servers = [ip for ip in self.mac_to_port if ip in self.server_ips]
            if available_servers:
                selected_server = random.choice(available_servers)
                self.lb_map[client_ip] = selected_server
                log.info("Server selected for client %s: %s" % (client_ip, selected_server))
            else:
                log.error("No available servers for client %s" % client_ip)


def launch(ip, servers):
    log.info("Loading Simple Load Balancer module")
    server_ips = servers.split(',')
    core.registerNew(SimpleLoadBalancer, ip, server_ips)