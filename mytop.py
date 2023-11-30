#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   listenPort=6633,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)


    info('*** Add hosts\n')
    hosts = {}
    for i in range(1, 7):
        host_name = 'h{}'.format(i)
        ip_address = '10.0.0.{}'.format(i)
        hosts[host_name] = net.addHost(host_name, cls=Host, ip=ip_address, defaultRoute=None)

    info('*** Add links\n')
    for host in hosts.values():
        net.addLink(host, s1)



    info( '*** Starting network\n')
    net.build()


    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])

    info('*** Starting HTTP servers on hosts h1 to h4\n')
    for i in range(1, 5):
        host_name = 'h{}'.format(i)
        host = hosts[host_name]
        host.cmd('python3 -m http.server 80 &')


    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

