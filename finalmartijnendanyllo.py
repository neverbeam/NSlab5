## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:
import sys
import struct
import select
from socket import *
from random import randint
from gui import MainWindow
from sensor import *
import threading


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

    # -- make the gui --
    global window
    window = MainWindow()
    window.writeln( 'my address is %s:%s' % peer.getsockname() )
    window.writeln( 'my position is (%s, %s)' % sensor_pos )
    window.writeln( 'my sensor value is %s' % sensor_val )

    global father
    father = peer.getsockname()[1]
    # List of all the neighbors
    global neighbors
    # List of all the neighbors
    neighbors = {}
    # lookuptable {(initiator,sequence): [echocnt,echoreply,payload]}
    global lookuptable
    lookuptable = {}
     # sequence based on amount of echos sent
    global echosequence
    echosequence = -1  #starts at -1 to become 0 at first echo wave sent
    # start looking for neighbors when entering
    neighbordiscovery(peer, False)
    # -- This is the event loop. --
    while window.update():
        guiline = window.getline()
        # If an command is typed in the gui give the right output.
        if guiline:
            guiaction(guiline, window, peer)
        # Selector module, readytowrite = neighbors
        readytoread, readytowrite, error = select.select([mcast, peer], [peer], [])
        for i in readytoread:
            message, addres = i.recvfrom(2048)
            a = peer.getsockname()[1]
            # Somehow multicast send message to itsself too, so those are filtered.
            if (addres[1] != a):
                type, sequence, (ix, iy), (nx, ny), operation, capability, payload = message_decode(message)

                # Received a ping message.
                if type == 0:
                    print "received ping"
                    comparerange(ix, iy, addres, peer)

                # Received pong message.
                if type == 1:
                    print "received pong"
                    neighbors[addres] = (nx,ny)
                    print neighbors

                # Received an echo message.
                elif type == 2:
                    window.writeln("received echo from  " + str((ix, iy))  )
                    echoReceive(peer, addres, (ix, iy), sequence, operation)

                # Received an echo reply.
                elif type == 3:
                    window.writeln("received echo_reply from " + str((nx, ny)))
                    echoReply(peer, (ix, iy), sequence, operation, payload)

# Send an echo to your neighbors.
def echoSend(peer, initiator, sequence, operation, payload=0):
    global neighbors
    for addres in neighbors:
        # Don't echo the message to your father.
        if addres !=  father:
            message = message_encode(MSG_ECHO, sequence, initiator, neighbors[addres], operation, 0, payload)
            peer.sendto(message, addres)

# Decide what to do after an echo has been received by this node.
def echoReceive(peer, addres, initiator, sequence, operation):
    global father
    global neighbors
    global value
    # Check wether I allready received this echo or not by looking at initiator pos and sequence number.
    if (initiator,sequence) not in lookuptable:
        # save father
        father = addres
        # echoreceived is 1 or higher, so set that it received this echo.
        lookuptable[(initiator,sequence)] = [1,0,0]
        # If the node is at the edge.
        if len(neighbors) == 1:
            if operation == OP_SIZE:
                lookuptable[(initiator,sequence)][2] = 1
            elif operation == OP_SUM:
                lookuptable[(initiator,sequence)][2] = value
            elif operation == OP_MIN or operation == OP_MAX:
                lookuptable[(initiator,sequence)][2] = value
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, lookuptable[(initiator,sequence)][2])
            peer.sendto(message, father)
        # If the node is not at the edge, echo the message further.
        else:
            # Set the min/max value of the node at this moment at its own value.
            if operation == OP_MIN or operation == OP_MAX:
                lookuptable[(initiator,sequence)][2] = value
            echoSend(peer, initiator, sequence, operation)
    # Directly reply if I allready have got this echo message.
    else:
        if operation == OP_SIZE:
            payload = 0
        elif operation == OP_SUM or operation == OP_MAX:
            payload = 0
        elif operation == OP_MIN:
            payload = float("inf")
        elif operation == OP_NOOP:
            payload = 0
        message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0 , payload)
        peer.sendto(message, addres)

# Decide what to do after this node received an echo reply.
def echoReply(peer, initiator, sequence, operation, payload):
    global neighbors
    global value
    # Adding one to the echo replies of this node.
    lookuptable[(initiator,sequence)][1] = lookuptable[(initiator,sequence)][1] +  1
    # Change the payload according to the operation.
    if operation == OP_SIZE or operation == OP_SUM:
        lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + payload
    elif operation == OP_MIN:
        if payload < lookuptable[(initiator,sequence)][2]:
            lookuptable[(initiator,sequence)][2] = payload
    elif operation == OP_MAX:
        if payload > lookuptable[(initiator,sequence)][2]:
            lookuptable[(initiator,sequence)][2] = payload
    elif operation == OP_NOOP:
        lookuptable[(initiator,sequence)][2] = 0

    # len - 1 because you don't send a reply to your father.
    if len(neighbors) - 1 == lookuptable[(initiator,sequence)][1] and pos != initiator:
            global father
            if operation == OP_SIZE:
                lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + 1
            elif operation == OP_SUM:
                lookuptable[(initiator,sequence)][2] = lookuptable[(initiator,sequence)][2] + value
            elif operation == OP_NOOP:
                lookuptable[(initiator,sequence)][2] = 0
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, lookuptable[(initiator,sequence)][2])
            peer.sendto(message, father)

    # initiation node heeft exacte aantal buren
    elif len(neighbors) == lookuptable[(initiator,sequence)][1] and pos == initiator:
            print "echo successful"
            if operation == OP_SIZE:
                window.writeln(str(lookuptable[(initiator,sequence)][2] + 1 ))
            elif operation == OP_SUM:
                window.writeln("Sum of the sensor values: " + str(lookuptable[(initiator,sequence)][2] + value))
            elif operation == OP_MIN:
                window.writeln("The smallest sensor value is: " + str(lookuptable[(initiator,sequence)][2]))
            elif operation == OP_MAX:
                window.writeln("The largest sensor value is: " + str(lookuptable[(initiator,sequence)][2]))

# Looks wether the node is in the range of the network
def comparerange(xi, yi, addres, peer):
    # If within range
    if ((pos[0] - xi) ** 2 + (pos[1] - yi)**2) ** 0.5 < args.range:
        message = message_encode(1,0,(xi,yi),pos)
        print "send pong"
        peer.sendto(message,addres)

# Looks for the neighbors in the network.
def neighbordiscovery(peer,restart):
    global neighbors
    message = message_encode(MSG_PING,0,pos,pos)
    peer.sendto(message, mcast_addr)
    # Sends a Ping message every x amount of seconds.
    Timingthis = threading.Timer(10, neighbordiscovery, [peer, False])
    # making sure that thread closes after exit on gui.
    Timingthis.daemon = True
    if restart:
        Timingthis.cancel()
    else:
        Timingthis.start()

# After an command has been given to the gui, action is required.
def guiaction(input, window, peer):
    global pos
    global father
    if input == "ping":
        message = message_encode(MSG_PING,0,pos,pos)
        peer.sendto(message, mcast_addr)
    elif input == "list":
        window.writeln("(Ip adres,port), (xposition, ypostion) of the neighbors: " + str(neighbors))
    elif input == "move":
        pos = random_position(args.grid)
        window.writeln("moved to: " + str(pos))
        neighbordiscovery(peer, True)
    elif input[0:3] == "set":
        if (input == "set add" and args.range < 70):
            args.range += 10
            window.writeln("the radius of the network is now: " + str(args.range))
        elif input == "set substract" and args.range > 20:
            args.range -= 10
            window.writeln("the radius of the network is now: " + str(args.range))
        else:
            window.writeln("not possible")
    elif input == "echo":
        father = peer.getsockname()[1]
        global echosequence
        echosequence += 1
        # Set the table for this echo.
        lookuptable[(pos,echosequence)] = [0, 0, 0]
        print echosequence
        echoSend(peer, pos, echosequence, OP_NOOP)
    elif input == "size":
        father = peer.getsockname()[1]
        echosequence += 1
        # Set the table for this echo.
        lookuptable[(pos,echosequence)] = [0, 0, 0]
        echoSend(peer, pos, echosequence, OP_SIZE)
    elif input == "value":
        global value
        value = randint(0, 100)
        window.writeln("This sensor's value is now " + str(value))
    elif input == "sum":
        father = peer.getsockname()[1]
        echosequence += 1
        # Set the table for this echo.
        lookuptable[(pos,echosequence)] = [0, 0, 0]
        echoSend(peer, pos, echosequence, OP_SUM)
    elif input == "same":
        print "hoi"
    elif input == "min":
        father = peer.getsockname()[1]
        echosequence += 1
        # Set the table for this echo.
        lookuptable[(pos,echosequence)] = [0, 0, value]
        echoSend(peer, pos, echosequence, OP_MIN, float("inf"))
    elif input == "max":
        father = peer.getsockname()[1]
        echosequence += 1
        # Set the table for this echo.
        lookuptable[(pos,echosequence)] = [0, 0, value]
        echoSend(peer, pos, echosequence, OP_MAX)
    else:
        window.writeln("Incorrect input!")


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
