from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.addresses import EthAddr, IPAddr

log = core.getLogger()

class FlowRuleManager:
    def __init__(self, connection, lb_mac, lb_ip):
        self.connection = connection
        self.lb_mac = lb_mac
        self.lb_ip = lb_ip
    
    def send_packet_out(self,buffer_id, src_mac, dst_mac, src_ip, dst_ip, outport, inport, payload):
        """
        Helper function to construct and send a packet_out message.
        """
        e = ethernet(type=ethernet.IP_TYPE, src=src_mac, dst=dst_mac)
        e.set_payload(payload)

        msg = of.ofp_packet_out()
        msg.buffer_id = buffer_id
        msg.data = e.pack()
        msg.in_port = inport

        msg.actions.append(of.ofp_action_dl_addr.set_src(src_mac))
        msg.actions.append(of.ofp_action_dl_addr.set_dst(dst_mac))

        msg.actions.append(of.ofp_action_nw_addr.set_src(src_ip))
        msg.actions.append(of.ofp_action_nw_addr.set_dst(dst_ip))

        msg.actions.append(of.ofp_action_output(port=outport))

        self.connection.send(msg)