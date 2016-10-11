## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:

from socket import *
import subprocess
import sys
import time

# Open socket to send and receive information

server = socket(AF_INET, SOCK_DGRAM)
server.bind(('', 8080))
print "server is up"

def main(nodes, r, steps):
    # kijken of steps of zonder steps command wordt gegeven
    processes = []
    if steps:
        # making the first node
        p = subprocess.Popen(['python', 'lab5-martijn.py', "--range", str(r)])
        processes.append(p)
        # checking its addres
        a, addr = server.recvfrom(2048)
        # If there is only 1 node, we dont need to check the size
        if nodes == 1:
            print "the single node is connected ofcourse"
        else:
            for node in range(nodes-1):
                p = subprocess.Popen(['python', 'lab5-martijn.py', "--range", str(r)])
                processes.append(p)
                # checking its addres
                a, addr = server.recvfrom(2048)
                time.sleep(3)
                server.sendto("size", addr)
                # receiving the size
                a, addr = server.recvfrom(2048)
                print "Added a node. The total amount of nodes is now: ", node + 2
                if (float(a) == node + 2):
                    print "All nodes in the network are connected"
                else:
                    print "not all nodes are connected in the network right now"

    else:
        # Store processes.

        for node in range(nodes):

            # Open a process.
            p = subprocess.Popen(['python', 'lab5-martijn.py', "--range", str(r)])
            processes.append(p)
            # checking its addres
            a, addr = server.recvfrom(2048)

        print "nodes are finding neighbors right now"
        time.sleep(3)
        server.sendto("size", addr)
        a, addr = server.recvfrom(2048)
        # Als het netwerk even groot is als aantal nodes, bereken min,max,sum
        if (float(a) == nodes):
            print "All the nodes in the network are connected"
            server.sendto("sum", addr)
            sum, addr = server.recvfrom(2048)
            print sum
            server.sendto("min", addr)
            min, addr = server.recvfrom(2048)
            print min
            server.sendto("max", addr)
            max, addr = server.recvfrom(2048)
            print max

        else:
            print "Not all the nodes are in the network."

    for process in processes:
        process.kill()

if __name__ == '__main__':
    import sys, argparse
    p = argparse.ArgumentParser()
    p.add_argument('--nodes', help='number of nodes to spawn', required=True, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--steps', help='output graph info every step', action="store_true")
    args = p.parse_args(sys.argv[1:])
    main(args.nodes, args.range, args.steps)
