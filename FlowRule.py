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

    def install_client_to_server(self, outport, client_ip, server_ip, server_mac, buffer_id=of.NO_BUFFER):
        """
        Installs a flow rule to forward traffic from a client to a server.
        """
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(
            dl_type=ethernet.IP_TYPE,
            nw_src=client_ip,
            nw_dst=self.lb_ip
        )
        msg.idle_timeout=3
        msg.hard_timeout=1
        msg.command=of.OFPFC_ADD
        msg.buffer_id = buffer_id
        msg.actions.append(of.ofp_action_dl_addr.set_src(self.lb_mac))
        msg.actions.append(of.ofp_action_dl_addr.set_dst(server_mac))
        msg.actions.append(of.ofp_action_nw_addr.set_dst(server_ip))
        msg.actions.append(of.ofp_action_output(port=outport))
        self.connection.send(msg)
        log.info("Flow rule installed: Client %s to Server %s" % (client_ip, server_ip))

        

    def install_server_to_client(self, outport, server_ip, client_ip, client_mac, buffer_id=of.NO_BUFFER):
        """
        Installs a flow rule to forward traffic from a server back to a client.
        """
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(
            dl_type=ethernet.IP_TYPE,
            nw_src=server_ip,
            nw_dst=client_ip
        )
        msg.idle_timeout=10
        msg.command=of.OFPFC_ADD
        msg.buffer_id = buffer_id
        msg.actions.append(of.ofp_action_dl_addr.set_src(self.lb_mac))
        msg.actions.append(of.ofp_action_dl_addr.set_dst(client_mac))
        msg.actions.append(of.ofp_action_nw_addr.set_src(self.lb_ip))
        msg.actions.append(of.ofp_action_output(port=outport))
        self.connection.send(msg)
        log.info("Flow rule installed: Server %s to Client %s" % (server_ip, client_ip))
    
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