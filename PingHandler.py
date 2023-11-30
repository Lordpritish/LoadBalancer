from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.icmp import icmp, echo, TYPE_ECHO_REQUEST

log = core.getLogger()

class PingHandler:
    def __init__(self, lb_mac, lb_ip):
        self.lb_mac = lb_mac          # Load balancer's fake MAC address
        self.lb_ip = lb_ip            # Load balancer's IP address

    def send_ping_request(self,connection, host_ip,host_mac):
        # Create an Ethernet frame
        eth_pkt = ethernet()
        eth_pkt.src = self.lb_mac  # replace with the source MAC address
        eth_pkt.dst = host_mac  # replace with the destination MAC address
        eth_pkt.type = ethernet.IP_TYPE

        # Create an IPv4 packet
        ip_pkt = ipv4()
        ip_pkt.srcip = self.lb_ip  # replace with the source IP address
        ip_pkt.dstip = host_ip  # replace with the destination IP address
        ip_pkt.protocol = ipv4.ICMP_PROTOCOL

        # Create an ICMP (ping) packet
        icmp_pkt = icmp()
        icmp_pkt.type = TYPE_ECHO_REQUEST
        icmp_pkt.payload = echo(id=1, seq=1)

        # Set the packet payloads
        ip_pkt.payload = icmp_pkt
        eth_pkt.payload = ip_pkt

        # Create an OpenFlow packet_out message and send the packet
        msg = of.ofp_packet_out()
        msg.data = eth_pkt.pack()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        connection.send(msg)
        log.info("Ping request sent to %s", host_ip)

