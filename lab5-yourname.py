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
    father = peer.getsockname()
    global neighbors
    neighbors = {}
    global echocnt
    echocnt = 0
    global echoreplies
    echoreplies = 0
    global initiationnode
    initiationnode = False
    global echosequence # sequence based on amount of echos sent
    echosequence = -1  #starts at -1 to become 0 at first echo wave sent
    global payloadtot
    payloadtot = 0;
    neighbordiscovery(peer, False)
    # -- This is the event loop. --
    while window.update():
        guiline = window.getline()
        if guiline:
            guiaction(guiline, window, peer)
        # Selector module, readytowrite = neighbors
        readytoread, readytowrite, error = select.select([mcast, peer], [peer], [])
        for i in readytoread:
            message, addres = i.recvfrom(2048)
            a = peer.getsockname()[1]
            # somehow multicast send message to itsself too
            if (addres[1] != a):
                type, sequence, (ix, iy), (nx, ny), operation, capability, payload = message_decode(message)
                # received a ping message.
                if type == 0:
                    print "received ping"
                    comparerange(ix, iy, addres, peer)

                # pong message
                if type == 1:
                    print "received pong"
                    neighbors[addres] = (nx,ny)
                    print neighbors

                elif type == 2:
                    window.writeln("received echo from  " + str((ix, iy))  )
                    echocnt += 1
                    echoReceive(peer, addres, (ix, iy), sequence, operation, payload)

                elif type == 3:
                    window.writeln("received echo_reply from " + str((nx, ny)))
                    echoreplies += 1
                    echoReply(peer, (ix, iy), sequence, operation, payload)

def echoSend(peer, initiator, sequence, operation, payload=0):
    global initiationnode
    if pos == initiator:
        initiationnode = True
    global neighbors
    # geen echo terug naar father
    for addres in neighbors:
        if addres !=  father:
            message = message_encode(MSG_ECHO, sequence, initiator, neighbors[addres], operation, 0, payload)
            peer.sendto(message, addres)


def echoReceive(peer, addres, initiator, sequence, operation, payload):
    global echocnt
    global father
    global totalzeroecho
    global neighbors
    global value
    if echocnt == 1:
        father = addres # save father
        if len(neighbors) == 1:
            if operation == OP_SIZE:
                payload = 1
            elif operation == OP_SUM:
                payload = value
            elif operation == OP_MIN or operation == OP_MAX:
                payload = value
            elif operation == OP_SAME:
                if payload == value:
                    payload = 1
                else:
                    payload = 0
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, payload)
            print(message_decode(message))
            peer.sendto(message, father)
            echocnt = 0
        else:
            echoSend(peer, initiator, sequence, operation, payload)
    else:
        if operation == OP_SIZE:
            payload = 0
        elif operation == OP_SUM or operation == OP_MAX:
            payload = 0
        elif operation == OP_MIN:
            payload = float("inf")
        elif operation == OP_SAME:
            payload = 0
        message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0 , payload)
        print(message_decode(message))
        peer.sendto(message, addres)

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
        if payload > value:
            payloadtot = value
        else:
            payloadtot = payload
    elif operation == OP_MAX:
        if payload < value:
            payloadtot = value
        else:
            payloadtot = payload
    elif operation == OP_SAME:
        payloadtot = payloadtot + payload
    #else:
    #    payloadtot = 0
    # len - 1 omdat de father geen reply stuurt.
    if len(neighbors) - 1 == echoreplies and initiationnode == False:
            global father
            if operation == OP_SIZE:
                payloadtot += 1
            elif operation == OP_SUM:
                payloadtot += value
            elif operation == OP_MIN:
                if payload > value:
                    payloadtot = value
                else:
                    payloadtot = payload
            elif operation == OP_MAX:
                if payload < value:
                    payloadtot = value
                else:
                    payloadtot = payload
            elif operation == OP_SAME:
                payloadtot += payload
            message = message_encode(MSG_ECHO_REPLY, sequence, initiator, pos, operation, 0, payloadtot)
            print(message_decode(message))
            peer.sendto(message, father)
            echoreplies = 0
            echocnt = 0
            #payloadtot = 0
    # initiation node heeft exacte aantal buren
    elif len(neighbors) == echoreplies and initiationnode == True:
            print "echo successful", payloadtot
            if operation == OP_SIZE:
                window.writeln(str(payloadtot + 1 ))
            elif operation == OP_SUM:
                window.writeln("Sum of the sensor values: " + str(payloadtot + value))
            elif operation == OP_MIN:
                if payload > value:
                    payloadtot = value
                else:
                    payloadtot = payload
                window.writeln("The smallest sensor value is: " + str(payloadtot))
            elif operation == OP_MAX:
                if payload < value:
                    payloadtot = value
                else:
                    payloadtot = payload
                window.writeln("The largest sensor value is: " + str(payloadtot))
            elif operation == OP_SAME:
                payloadtot += payload
                window.writeln("Amount of sensors with the same value: " + str(payloadtot))
            echoreplies = 0
            echocnt = 0
            payloadtot = 0
            initiationnode = False


def comparerange(xi, yi, addres, peer):
    # If within range
    if ((pos[0] - xi) ** 2 + (pos[1] - yi)**2) ** 0.5 < args.range:
        message = message_encode(1,0,(xi,yi),pos)
        print "send pong"
        peer.sendto(message,addres)


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

def guiaction(input, window, peer):
    global pos
    global payloadtot
    global father
    global value
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
        father = peer.getsockname()
        global echosequence
        echosequence += 1
        print echosequence
        echoSend(peer, pos, echosequence, OP_NOOP)
    elif input == "size":
        father = peer.getsockname()
        echosequence += 1
        payloadtot = 0;
        echoSend(peer, pos, echosequence, OP_SIZE)
    elif input == "value":
        global value
        value = randint(0, 100)
        window.writeln("This sensor's value is now " + str(value))
    elif input == "sum":
        father = peer.getsockname()
        echosequence += 1
        payloadtot = 0
        echoSend(peer, pos, echosequence, OP_SUM)
    elif input == "same":
        father = peer.getsockname()
        echosequence += 1
        payloadtot = 0
        echoSend(peer, pos, echosequence, OP_SAME, value)
    elif input == "min":
        father = peer.getsockname()
        echosequence += 1
        payloadtot = 0
        echoSend(peer, pos, echosequence, OP_MIN, float("inf"))
    elif input == "max":
        father = peer.getsockname()
        echosequence += 1
        payloadtot = 0
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
    p.add_argument('--value', help='sensor value', default=50, type=int)
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
