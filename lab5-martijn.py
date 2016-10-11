## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: Martijn Dortmond en
## STUDENT ID: 10740406 en

import sys
import struct
import select
from socket import *
from random import randint
from sensor import *
import threading
import time

# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


def main(mcast_addr,
    sensor_pos, sensor_range, sensor_val,
    grid_size, ping_period):
    """
    mcast_addr: udp multicast (ip, port) tuple.
    sensor_pos: (x,y) sensor position tuple.
    sensor_range: range of the sensor ping (radius).
    sensor_val: sensor value.
    grid_size: length of the  of the grid (which is always square).
    ping_period: time in seconds between multicast pings.
    """

    # -- Create the multicast listener socket. --
    mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    # Sets the socket address as reusable so you can run multiple instances
    # of the program on the same machine at the same time.
    mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # Subscribe the socket to multicast messages from the given address.
    mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
    mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
    if sys.platform == 'win32': # windows special case
        mcast.bind( ('', mcast_addr[1]) )
    else: # should work for everything else
        mcast.bind(mcast_addr)


    # -- Create the peer-to-peer socket. --
    peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    # Set the socket multicast TTL so it can send multicast messages.
    peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
    # Bind the socket to a random port.
    if sys.platform == 'win32': # windows special case
        peer.bind( ('', INADDR_ANY) )
    else: # should work for everything else
        peer.bind( ('', INADDR_ANY) )

    # sending our ip adrres when connection starts.
    peer.sendto("connection", ('', 8080))

    father = peer.getsockname()[1]
    global neighbors
    global initiationnode
    global echosequence # sequence based on amount of echos sent
    global lookuptable
    lookuptable = {}
    initiationnode = False
    echosequence = -1  #starts at -1 to become 0 at first echo wave sent
    #Looking for the neighbors in the network.
    neighbordiscovery(peer, False)
    # -- This is the event loop. --
    while 1:
        # Selector module, readytowrite = neighbors
        readytoread, readytowrite, error = select.select([mcast, peer], [peer], [])
        for i in readytoread:
            message, addres = i.recvfrom(2048)
            a = peer.getsockname()[1]
            # If a message comes from overhead server, action is needed.
            if (addres == ('127.0.0.1',8080)):
                action(message, peer)
            # somehow multicast send message to itsself too, so filter those messages
            elif (addres[1] != a):
                type, sequence, (ix, iy), (nx, ny), operation, capability, payload = message_decode(message)
                # received a ping message.
                if type == 0:
                    comparerange(ix, iy, addres, peer)

                # received a pong message
                if type == 1:
                    neighbors[addres] = (nx,ny)

                # received an echo.
                elif type == 2:
                    echoReceive(peer, addres, (ix, iy), sequence, operation)

                # received an echo reply
                elif type == 3:
                    echoReply(peer, (ix, iy), sequence, operation, payload)

def echoSend(peer, initiator, sequence, operation, payload=0):
    global initiationnode
    global neighbors
    if pos == initiator:
        initiationnode = True
    # Send echo to all the neighbors.
    for addres in neighbors:
        # Don't echo to the father.
        if addres !=  father:
            message = message_encode(MSG_ECHO, sequence, initiator, neighbors[addres], operation, 0, payload)
            peer.sendto(message, addres)

# Whenever a echo is received it is send forward or an echoreply is sent back.
def echoReceive(peer, addres, initiator, sequence, operation):
    global father
    global neighbors
    global value
    # If the echocount = 1 then it's the first echo from the sequence/initiator
    if (initiator,sequence) not in lookuptable:
        lookuptable[(initiator,sequence)] = [1,0,0]
        # save father
        father = addres
        # If size neigbors = 1 than we are on an edge.
        if len(neighbors) == 1:
            if operation == OP_SIZE:
                payload = 1
            elif operation == OP_SUM:
                payload = value
            elif operation == OP_MIN or operation == OP_MAX:
                payload = value
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, payload)
            peer.sendto(message, father)
        # If we are not on an edge, send the message to your neighbors.
        else:
            if operation == OP_MIN or operation == OP_MAX:
                lookuptable[(initiator,sequence)][2] = value
            echoSend(peer, initiator, sequence, operation)
    # If it's a repeated echo, directly send an echo back.
    else:
        if operation == OP_SIZE:
            payload = 0
        elif operation == OP_SUM or operation == OP_MAX:
            payload = 0
        elif operation == OP_MIN:
            payload = float("inf")
        message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0 , payload)
        peer.sendto(message, addres)

# Whenever a echoreply is received, one is send back untill it arrives at the starting node.
def echoReply(peer, initiator, sequence, operation, payload):
    global initiationnode
    global neighbors
    global value
    lookuptable[(initiator,sequence)][1] = lookuptable[(initiator,sequence)][1] +  1
    if operation == OP_SIZE or operation == OP_SUM:
        lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + payload
    elif operation == OP_MIN:
        if payload < lookuptable[(initiator,sequence)][2]:
            lookuptable[(initiator,sequence)][2] = payload
    elif operation == OP_MAX:
        if payload > lookuptable[(initiator,sequence)][2]:
            lookuptable[(initiator,sequence)][2] = payload

    # If all neighbors are checked, send the echoreply back to the father.
    # len(neigbors-1) because no echoreply is comming form the father.
    if len(neighbors) - 1 == lookuptable[(initiator,sequence)][1] and initiationnode == False:
            global father
            if operation == OP_SIZE:
                lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + 1
            elif operation == OP_SUM:
                lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + value
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, lookuptable[(initiator,sequence)][2])
            peer.sendto(message, father)

    # The initiationnoe has the exact amount of neighbors because it has got no father.
    elif len(neighbors) == lookuptable[(initiator,sequence)][1] and initiationnode == True:
            if operation == OP_SIZE:
                # Also count the initiationnode so + 1
                peer.sendto(str(lookuptable[(initiator,sequence)][2] + 1), ('',8080))
            elif operation == OP_SUM:
                # Also count the value of the initiationnode
                peer.sendto("sum: " + str(lookuptable[(initiator,sequence)][2] + value),('',8080))
            elif operation == OP_MIN:
                peer.sendto("min: " + str(lookuptable[(initiator,sequence)][2]),('',8080))
            elif operation == OP_MAX:
                peer.sendto("max: " + str(lookuptable[(initiator,sequence)][2]), ('',8080))
            initiationnode = False

# check wether the node is in range of the network.
def comparerange(xi, yi, addres, peer):
    # Formula for the range of the network
    if ((pos[0] - xi) ** 2 + (pos[1] - yi)**2) ** 0.5 < args.range:
        message = message_encode(1,0,(xi,yi),pos)
        peer.sendto(message,addres)

# Check all the neighbors within a given range.
def neighbordiscovery(peer,restart):
    global neighbors
    neighbors = {}
    message = message_encode(MSG_PING,0,pos,pos)
    peer.sendto(message, mcast_addr)
    # Sends a Ping message every x amount of seconds.
    Timingthis = threading.Timer(2, neighbordiscovery, [peer, False])
    # making sure that thread closes after exit on gui.
    Timingthis.daemon = True
    if restart:
        Timingthis.cancel()
    else:
        Timingthis.start()

# action needs to be taken after a message from the overhead server.
def action(input, peer):
    global pos
    global father
    global echosequence
    if input == "size":
        if len(neighbors) == 0:
            peer.sendto("1", ('',8080))
        else:
            father = peer.getsockname()[1]
            echosequence += 1
            lookuptable[(pos,echosequence)] = [0, 0, 0]
            echoSend(peer,pos,echosequence ,OP_SIZE)
    elif input == "sum":
        father = peer.getsockname()[1]
        echosequence += 1
        lookuptable[(pos,echosequence)] = [0, 0, 0]
        echoSend(peer, pos, echosequence, OP_SUM)
    elif input == "min":
        father = peer.getsockname()[1]
        echosequence += 1
        lookuptable[(pos,echosequence)] = [0, 0, value]
        echoSend(peer, pos, echosequence, OP_MIN, float("inf"))
    elif input == "max":
        father = peer.getsockname()[1]
        echosequence += 1
        lookuptable[(pos,echosequence)] = [0, 0, value]
        echoSend(peer, pos, echosequence, OP_MAX)



# -- program entry point --
if __name__ == '__main__':
    import sys, argparse
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.5')
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
        default=5, type=int)
    args = p.parse_args(sys.argv[1:])
    global pos
    if args.pos:
        pos = tuple( int(n) for n in args.pos.split(',')[:2] )
    else:
        pos = random_position(args.grid)
    global value
    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)
    mcast_addr = (args.group, args.port)
    main(mcast_addr, pos, args.range, value, args.grid, args.period)
