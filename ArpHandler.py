from pox.lib.packet.arp import arp
from pox.core import core
from pox.lib.packet.ethernet import ethernet
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

class ARPHandler:
    def __init__(self, lb_mac, lb_ip, ethernet_broad):
        self.lb_mac = lb_mac          # Load balancer's fake MAC address
        self.lb_ip = lb_ip            # Load balancer's IP address
        self.ethernet_broad = ethernet_broad  # Broadcast MAC address

    def send_proxied_arp_reply(self, packet, connection, outport, requested_mac):
        """
        Sends a proxied ARP reply to a client or server pretending to be the destination.
        """
        # log.debug("Sending proxied ARP reply:")
        # log.debug("  Packet: %s" % packet)
        # log.debug("  Source IP: %s, Destination IP: %s" % (packet.payload.protosrc, packet.payload.protodst))
        # log.debug("  Outport: %s" % outport)
        # log.debug("  Requested MAC: %s" % requested_mac)

        arp_reply = arp()
        arp_reply.hwtype = arp_reply.HW_TYPE_ETHERNET
        arp_reply.prototype = arp_reply.PROTO_TYPE_IP
        arp_reply.hwlen = 6
        arp_reply.protolen = 4
        arp_reply.opcode = arp.REPLY

        arp_reply.hwdst = packet.src
        arp_reply.hwsrc = requested_mac
        arp_reply.protosrc = packet.payload.protodst
        arp_reply.protodst = packet.payload.protosrc

        eth_frame = ethernet(type=ethernet.ARP_TYPE, src=requested_mac, dst=packet.src)
        eth_frame.set_payload(arp_reply)

        packet_out_msg = of.ofp_packet_out()
        packet_out_msg.data = eth_frame.pack()
        packet_out_msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
        packet_out_msg.in_port = outport

        # log.debug("Sending ARP reply packet_out_msg: %s" % packet_out_msg)
        
        connection.send(packet_out_msg)


    def send_proxied_arp_request(self, connection, ip):
        """
        Sends an ARP request to discover the MAC address of a specific IP.
        """
        arp_req = arp()
        arp_req.hwtype = arp_req.HW_TYPE_ETHERNET
        arp_req.prototype = arp_req.PROTO_TYPE_IP
        arp_req.hwlen = 6
        arp_req.protolen = 4
        arp_req.opcode = arp.REQUEST
        arp_req.hwdst = self.ethernet_broad
        arp_req.protodst = ip
        arp_req.hwsrc = self.lb_mac
        arp_req.protosrc = self.lb_ip

        ethernet_frame = ethernet(type=ethernet.ARP_TYPE, src=self.lb_mac, dst=self.ethernet_broad)
        ethernet_frame.set_payload(arp_req)

        msg = of.ofp_packet_out()
        msg.data = ethernet_frame.pack()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        connection.send(msg)