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
        mcast.bind( ('localhost', mcast_addr[1]) )
    else: # should work for everything else
        mcast.bind(mcast_addr)


    # -- Create the peer-to-peer socket. --
    peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    # Set the socket multicast TTL so it can send multicast messages.
    peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
    # Bind the socket to a random port.
    if sys.platform == 'win32': # windows special case
        peer.bind( ('localhost', INADDR_ANY) )
    else: # should work for everything else
        peer.bind( ('', INADDR_ANY) )

    # -- make the gui --
    window = MainWindow()
    window.writeln( 'my address is %s:%s' % peer.getsockname() )
    window.writeln( 'my position is (%s, %s)' % sensor_pos )
    window.writeln( 'my sensor value is %s' % sensor_val )

    global neighbors
    neighbordiscovery(peer)
    # -- This is the event loop. --
    while window.update():
        # Selector module, readytowrite = neighbors
        readytoread, readytowrite, error = select.select([mcast, peer], [peer], [0])
        for i in readytoread:
            try:
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
            except IndexError:
                pass

def comparerange(xi, yi, addres, peer):
    # If within range
    if ((pos[0] - xi)**2 + (pos[1] - yi)**2)**0.5 < args.range:
        message = message_encode(1,0,(xi,yi),pos)
        print "send pong"
        peer.sendto(message,addres)


def neighbordiscovery(peer):
    global neighbors
    neighbors = {}
    message = message_encode(MSG_PING,0,pos,pos)
    peer.sendto(message, mcast_addr)
    # Sends a Ping message every x amount of seconds.
    threading.Timer(4, neighbordiscovery, [peer]).start()

# -- program entry point --
if __name__ == '__main__':
    import sys, argparse
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1')
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
        default=5, type=int)
    args = p.parse_args(sys.argv[1:])
    if args.pos:
        pos = tuple( int(n) for n in args.pos.split(',')[:2] )
    else:
        pos = random_position(args.grid)
    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)
    mcast_addr = (args.group, args.port)
    main(mcast_addr, pos, args.range, value, args.grid, args.period)
