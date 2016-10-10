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
    global echocnt
    global echoreplies
    global initiationnode
    global echosequence # sequence based on amount of echos sent
    global payloadtot
    echocnt = 0
    echoreplies = 0
    initiationnode = False
    echosequence = -1  #starts at -1 to become 0 at first echo wave sent
    global payloadtot
    payloadtot = 0;
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
                    print "received ping"
                    comparerange(ix, iy, addres, peer)

                # received a pong message
                if type == 1:
                    print "received pong"
                    neighbors[addres] = (nx,ny)
                    print neighbors

                # received an echo.
                elif type == 2:
                    print "received echo from  " , str((ix, iy))
                    echocnt += 1
                    echoReceive(peer, addres, (ix, iy), sequence, operation)

                # received an echo reply
                elif type == 3:
                    print "received echo_reply from ", str((nx, ny))
                    echoreplies += 1
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
    global echocnt
    global father
    global totalzeroecho
    global neighbors
    global value
    # If the echocount = 1 then it's the first echo from the sequence/initiator
    if echocnt == 1:
        father = addres # save father
        # If size neigbors = 1 than we are on an edge.
        if len(neighbors) == 1:
            if operation == OP_SIZE:
                payload = 1
            elif operation == OP_SUM:
                payload = value
            elif operation == OP_MIN or operation == OP_MAX:
                payload = value
            print "echo send at edge"
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, payload)
            peer.sendto(message, father)
            echocnt = 0
        # If we are not on an edge, send the message to your neighbors.
        else:
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
    global echoreplies
    global initiationnode
    global neighbors
    global payloadtot
    global echocnt
    global value
    if operation == OP_SIZE or operation == OP_SUM:
        payloadtot = payloadtot + payload
    elif operation == OP_MIN:
        # check wether the neigbors nodes are smaller.
        if payload > value:
            payloadtot = value
        else:
            payloadtot = payload
    elif operation == OP_MAX:
        # check wether the neigbors nodes are bigger.
        if payload < value:
            payloadtot = value
        else:
            payloadtot = payload
    #else op noop?
    #    payloadtot = 0

    # If all neighbors are checked, send the echoreply back to the father.
    # len(neigbors-1) because no echoreply is comming form the father.
    if len(neighbors) - 1 == echoreplies and initiationnode == False:
            global father
            if operation == OP_SIZE:
                payloadtot += 1
            elif operation == OP_SUM:
                payloadtot += value
            elif operation == OP_MIN:
                if payload > value:
                    payloadtot = value
            elif operation == OP_MAX:
                if payload < value:
                    payloadtot = value
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, payloadtot)
            peer.sendto(message, father)
            echoreplies = 0
            echocnt = 0
            #payloadtot = 0
    # The initiationnoe has the exact amount of neighbors because it has got no father.
    elif len(neighbors) == echoreplies and initiationnode == True:
            if operation == OP_SIZE:
                # Also count the initiationnode so + 1
                peer.sendto(str(payloadtot + 1), ('',8080))
            elif operation == OP_SUM:
                # Also count the value of the initiationnode
                peer.sendto("sum: " + str(payloadtot + value),('',8080))
            elif operation == OP_MIN:
                if payload > value:
                    payloadtot = value
                peer.sendto("min: " + str(payloadtot),('',8080))
            elif operation == OP_MAX:
                if payload < value:
                    payloadtot = value
                peer.sendto("max: " + str(payloadtot), ('',8080))
            # resetting the connection.
            echoreplies = 0
            echocnt = 0
            payloadtot = 0
            initiationnode = False

# check wether the node is in range of the network.
def comparerange(xi, yi, addres, peer):
    # Formula for the range of the network
    if ((pos[0] - xi) ** 2 + (pos[1] - yi)**2) ** 0.5 < args.range:
        message = message_encode(1,0,(xi,yi),pos)
        print "send pong"
        peer.sendto(message,addres)

# Check all the neighbors within a given range.
def neighbordiscovery(peer,restart):
    global neighbors
    neighbors = {}
    message = message_encode(MSG_PING,0,pos,pos)
    peer.sendto(message, mcast_addr)
    # Sends a Ping message every x amount of seconds.
    Timingthis = threading.Timer(4, neighbordiscovery, [peer, False])
    # making sure that thread closes after exit on gui.
    Timingthis.daemon = True
    if restart:
        Timingthis.cancel()
    else:
        Timingthis.start()

# action needs to be taken after a message from the overhead server.
def action(input, peer):
    global pos
    global payloadtot
    global father
    global echosequence
    if input == "size":
        if len(neighbors) == 0:
            peer.sendto("1", ('',8080))
        else:
            print "size action"
            father = peer.getsockname()[1]
            echosequence += 1
            payloadtot = 0;
            echoSend(peer,pos,echosequence ,OP_SIZE)
    elif input == "sum":
        father = peer.getsockname()[1]
        echosequence += 1
        payloadtot = 0
        echoSend(peer, pos, echosequence, OP_SUM)
    elif input == "min":
        father = peer.getsockname()[1]
        echosequence += 1
        payloadtot = 0
        echoSend(peer, pos, echosequence, OP_MIN, float("inf"))
    elif input == "max":
        father = peer.getsockname()[1]
        echosequence += 1
        payloadtot = 0
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
