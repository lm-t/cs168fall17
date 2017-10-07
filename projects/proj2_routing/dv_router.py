"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter(basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.table = {} #key=host value=(latency, port, time, oldPort)
        self.portLatency = {} #list of link latencies that router has
        self.directRoute = {}

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Add link to list of links
        self.portLatency[port] = latency

        # Send table through RoutePackets to link
        for host in self.table:
            hostVector = self.table[host]
            self.send(basics.RoutePacket(host, hostVector[0]), port)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        #remove link
        del self.portLatency[port]
        for host, hostVector in self.table.items():
            if hostVector[1] == port:
                if self.POISON_MODE:
                    #route poison
                    self.send(basics.RoutePacket(host, INFINITY), port, flood=True)
                    self.table[host] = (INFINITY, hostVector[1], hostVector[2], hostVector[3])
                #remove from table
                del self.table[host]
                #direct route fallback
                if host in self.directRoute:
                    self.table[host] = self.directRoute[host]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            #if host is not in table
            if packet.destination not in self.table:
                #add host to table with (link latency + this latency) and current time
                newLatency = packet.latency + self.portLatency[port]
                self.table[packet.destination] = (newLatency, port, api.current_time(), port)
                #flood new host to other switches/routers
                self.send(basics.RoutePacket(packet.destination, newLatency), port, flood=True)
            #else try to update vector
            else:
                hostVector = self.table[packet.destination]
                originalLatency = hostVector[0]
                newLatency = packet.latency + self.portLatency[port]
                if self.directRoute.has_key(packet.destination) and self.directRoute[packet.destination][0] < originalLatency:
                    #update to direct route if possible
                    self.table[packet.destination] = self.directRoute[packet.destination]
                elif hostVector[1] == port:
                    #update time
                    if newLatency > originalLatency:
                        #update latency
                        self.table[packet.destination] = (newLatency, hostVector[1], api.current_time(), hostVector[3])
                        self.send(basics.RoutePacket(packet.destination, newLatency), port, flood=True)
                    else:
                        self.table[packet.destination] = (originalLatency, hostVector[1], api.current_time(), hostVector[3])
                elif newLatency <= originalLatency:
                    #update vector with lower latency
                    self.table[packet.destination] = (newLatency, port, api.current_time(), originalLatency)

        elif isinstance(packet, basics.HostDiscoveryPacket):
            #add host to table
            hostVector = (self.portLatency[port], port, None, port)
            self.table[packet.src] = hostVector
            self.directRoute[packet.src] = hostVector
            #send host to other links
            self.send(basics.RoutePacket(packet.src, hostVector[0]), port, flood=True)

        else:
            #forward regular packet
            isHairpin = packet.src != packet.dst #need to better implement
            isIntable = packet.dst in self.table
            if isinstance(packet.dst, api.HostEntity) and isHairpin and isIntable:
                hostPort = self.table[packet.dst][1]
                hostLatency = self.table[packet.dst][0]
                if not hostLatency >= INFINITY:
                    self.send(packet, hostPort)


    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        # Part 1: Send RoutePackets to neighbors
        for host, hostVector in self.table.items():
        # Part 2: Update any expired entries
            #if host has no time -> flood
            if hostVector[2] == None:
                self.send(basics.RoutePacket(host, hostVector[0]), hostVector[1], flood=True)
            elif api.current_time() - hostVector[2] < self.ROUTE_TIMEOUT:
                #flood tables to neighbors
                self.send(basics.RoutePacket(host, hostVector[0]), hostVector[1], flood=True)
            else:
                #remove expired entries
                del self.table[host]
