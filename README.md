# LoadBalancer

## Team Members:
- **Pritish Panda (1005970914)**
- **Yuto Omachi (1006005163)**
- **Shannon Budiman (1006863770)**

## Table of Contents
- [Project Proposal: Load Balancer with Dynamic Algorithm Selection Using POX and Mininet in an SDN Environment](#project-proposal-load-balancer-with-dynamic-algorithm-selection-using-pox-and-mininet-in-an-sdn-environment)
- [Specific Goals and Targets](#specific-goals-and-targets)
- [Tentative Timeline with Clear Goals and Targets](#tentative-timeline-with-clear-goals-and-targets)
- [How the Project Relates to the Field of "Computer Networks"](#how-the-project-relates-to-the-field-of-computer-networks)
- [Installation Steps](#installation-steps)


# Project Proposal: Load Balancer with Dynamic Algorithm Selection Using POX and Mininet in an SDN Environment

## Project Description and Rationale:
This project aims to implement a load balancer using Software-Defined Networking (SDN) principles, with a specific focus on the POX SDN controller and the Mininet network emulator. The rationale behind this project is to explore how SDN can enhance network performance through load balancing and gain practical experience in SDN application development. This project will include the ability to dynamically select and run different load balancing algorithms.

## Specific Goals and Targets:
1. **Load Balancing Logic**: Develop and implement multiple load balancing algorithms (e.g., round-robin, least connections) within the POX SDN controller to distribute incoming network traffic across multiple backend servers.

2. **Dynamic Algorithm Selection**: Create a dynamic configuration method that allows users to select and switch between different load balancing algorithms during runtime.

3. **Flow Rule Definition**: Use the OpenFlow protocol supported by the POX controller to define flow rules for directing network packets to backend servers based on the selected load balancing algorithm.

4. **Basic Testing**: Conduct initial testing using Mininet to verify that the load balancer performs load distribution correctly for each selected algorithm.

5. **Documentation**: Create concise project documentation that covers architecture, design decisions, and usage instructions for the load balancer with dynamic algorithm selection.

6. **User Interface (UI) Development**: Develop a user-friendly web-based UI that allows users to configure, monitor, and interact with the load balancer, including dynamic algorithm selection.

## Tentative Timeline with Clear Goals and Targets:
- **Week 1**: Project setup, research on load balancing algorithms, initial design of the network topology.
- **Week 2**: Implementation of load balancing logic for multiple algorithms, dynamic algorithm selection, and the beginning of testing.
- **Week 3**: Continued testing, UI development, and configuration method.
- **Week 4**: Final testing, refinement, documentation completion, and project wrap-up.


## How the Project Relates to the Field of "Computer Networks":
This project aligns with the field of computer networks by addressing the fundamental concept of load balancing within SDN. It demonstrates the potential of SDN technologies in providing flexible and dynamic load balancing solutions for various network scenarios.
Here's the corrected version:


# Installation Steps

## Start Mininet VM

Ensure that the VM is connected to the internet.

## Prerequisites

Make sure you have the following prerequisites and fixes installed on the Mininet VM:

1. **Update the package list:**
   
   ```bash
   sudo apt-get update
   ```

2. **Install curl:**
   
   ```bash
   sudo apt-get install curl
   ```

3. **Fix this line of code in `./pox/lib/packet/packet_utils.py`:**
   
   Update the line around 105 in check_sum function , fixes a type conversion err :
   ```python
   # start += struct.unpack('H', data[-1]+'\0')[0] # Specify order?
   ```
   to:
   ```python
   start += struct.unpack('H', bytes([data[-1], 0]))[0]
   ```

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/Lordpritish/LoadBalancer.git
   ```

2. Copy the all files except mytop.py from the repository into the POX extension folder:

   ```bash
   cp [<repository_folder>/*(except mytop.py)] ./pox/ext/
   ```
4. Copy the `mytop.py`` from the repository into the mininet exmaples folder:

   ```bash
   cp <repository_folder>/mytop.py ~/mininet/examples/
   ```

## Running the Load Balancer


This POX controller implements both Static and Dyanamic load balancing algorithm. It supports 4 load balancing algorithms:

1. **Random Balancer (`RANDOM`):** Servers are selected randomly.

2. **Round Robin Balancer (`ROUND_ROBIN`):** Servers are selected in a circular sequence.

3. **Weighted Round Robin Balancer (`WEIGHTED_ROUND_ROBIN`):** Servers are selected based on weights assigned to each server.

4. **Weighted response time (`LEAST_RESPONSE_TIME`):** Averages the response time of each server, and combines that with the number of connections each server has open to determine where to send traffic. 

## Running the Load Balancer Controller

To run the load balancer controller, use the following command:

```bash
./pox.py log.level --DEBUG LoadBalancer --ip=<controller_ip> --servers=<comma_separated_servers> --alg=<algorithm> --weights=<comma_separated_weights>
```

- `<controller_ip>`: IP address of the controller.
- `<comma_separated_servers>`: Comma-separated list of server IP addresses.
- `<algorithm>`: (Optional) Load balancing algorithm. Available options: 1=`RANDOM`, 2=`ROUND_ROBIN`, 3=`WEIGHTED_ROUND_ROBIN`,
   4=`LEAST_RESPONSE_TIME`(default is 1=`RANDOM`).
- `<comma_separated_weights>`: (Optional) Comma-separated list of weights corresponding to each server (required for `WEIGHTED_ROUND_ROBIN` algorithm).

### Example Usage:

1. Navigate to the POX directory:

   ```bash
   cd ./pox
   ```

2. Terminate any existing controllers:

   ```bash
   sudo pox.py killall controller
   ```

3. Run the load balancer controller:

   ```bash
   ./pox.py log.level --DEBUG LoadBalancer --ip=10.0.1.1 --servers=10.0.0.1,10.0.0.2,10.0.0.3,10.0.0.4
   ```

   ```bash
   ./pox.py log.level --DEBUG LoadBalancer --ip=10.0.1.1 --servers=10.0.0.1,10.0.0.2,10.0.0.3,10.0.0.4 --alg=1
   ```

   ```bash
   ./pox.py log.level --DEBUG LoadBalancer --ip=10.0.1.1 --servers=10.0.0.1,10.0.0.2,10.0.0.3,10.0.0.4 --alg=3 --weights=1,2,3,4
   ```

   ```bash
   ./pox.py log.level --DEBUG LoadBalancer --ip=10.0.1.1 --servers=10.0.0.1,10.0.0.2,10.0.0.3,10.0.0.4 --alg=4 
   ```




## Running Mininet Example

1. Go to the root folder of the VM and navigate to the Mininet examples directory:

   ```bash
   cd ~/mininet/examples/
   ```

2. Clear any existing Mininet configurations:

   ```bash
   sudo mn -c
   ```

3. Run this command to use xterm
   ```bash
   sudo cp ~/.Xauthority ~root/
   ```

4. Run the Mininet topology:

   ```bash
   sudo python ./mytop.py
   ```

## Generating a Plot
1. After terminating LoadBalancer, it will generate req_count.txt file which contains log of which server the loader balancer redirected the request to.

2. Run the following command to generate a plot of total # of requests to each server over time

   ``` python3 <Path-to-UIGenerator.py> <Path-to_req_count.txt> ```

