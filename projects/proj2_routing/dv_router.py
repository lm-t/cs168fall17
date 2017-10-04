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
        self.table = [] #(host, latency, port, time)
        self.links = [] #list of links that router has

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Add link to list of links
        link = (port, latency)
        links.append(link)

        # Send table through RoutePackets to link
        for host in self.table:
            pass

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        #remove link
        for link in links:
            if link[0] == port:
                links.remove(link)
        #route poison
        if self.POISON_MODE:
            for host in self.table:
                if host[2] == port:
                    host[1] == INFINITY

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            #checks poisoned packet
            if packet.latency == INFINITY:
                d = packet.destination
            #send the packet back with poison
            if self.POISON_MODE:
                self.send(basics.RoutePacket(packet.destination, INFINITY), port)
            #if host is not in table
            if packet.destination not in self.table:
                #add destination with (link latency + this latency) and current time
            #else do minpath()
            else:
                pass

        elif isinstance(packet, basics.HostDiscoveryPacket):
            #add host to table
            host = (packet.src, self.link[port], port, None)
            self.table.append(host)
            #send host to other links
            self.send(basics.RoutePacket(host[0], host[1]), host[3], flood=True)


    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        # Part 1: Send RoutePackets to neighbors
        for link in links:
            pass
        # Part 2: Update any expired entries
