import wan_optimizer
from tcp_packet import Packet

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into fixed-size blocks.

    This WAN optimizer should implement part 1 of project 4.
    """

    # Size of blocks to store, and send only the hash when the block has been
    # sent previously
    BLOCK_SIZE = 8000

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).
        hashes = {} #key:value -> hash:block
        buffers = {} #key:value -> (source, destination):block
        return

    def receive(self, packet):
        """ Handles receiving a packet.

        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        def send_with_optimizer(hasch, is_fin):
            if hasch not in self.hashes.keys():
                self.hashes[hasch] = block_payload[:BLOCK_SIZE]
                send_multiple(hasch)
            else:
                #send optimal packet
                optimal_packet = tcp_packet.Packet(
                    packet_key[0],
                    packet_key[1],
                    False,
                    is_fin,
                    hasch,
                    hasch.size)
                self.send(optimal_packet, self.wan_port)
        def send_multiple(hasch, port, is_fin):
            block_payload = self.hashes[hasch]
            packets = []
            for i in range(0, len(block_payload), utils.MAX_PACKET_SIZE):
                pload = block_payload[i: i + utils.MAX_PACKET_SIZE]
                pckt = = tcp_packet.Packet(
                    packet_key[0],
                    packet_key[1],
                    True,
                    False,
                    pload,
                    pload.size)
                packets.append(pckt)
            if is_fin:
                packets[-1].is_fin = True
            for packet in packets:
                self.send(packet, port)
        #Case 1
        if packet.src in self.address_to_port and packet.dest in self.address_to_port:
            # The packet is from a client connected to this middlebox and
            # the packet is destined to a client connected to this middlebox
            self.send(packet, self.address_to_port[packet.dest])
        #Case 3
        elif packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            if packet.is_raw_data:
                packet_key = (packet.src, packet.dest)
                #add packet payload to block payload
                if packet_key not in self.buffers.keys():
                    self.buffers[packet_key] = packet.payload
                else:
                    block_payload = self.buffers[packet_key]
                    block_payload += packet.payload
                    self.buffers[packet_key] = block_payload
                #if buffer payload is full or is_fin
                block_payload = self.buffers[packet_key]
                if len(block_payload) > BLOCK_SIZE and packet.is_fin:
                    remainder = block_payload[BLOCK_SIZE:]
                    #add block payload to hashes
                    hasch = utils.get_hash(block_payload[:BLOCK_SIZE])
                    self.hashes[hasch] = block_payload[:BLOCK_SIZE]
                    #!!!send_multiple!!!
                    #add remainder payload to hashes
                    remainder_hash = utils.get_hash(remainder)
                    self.hashes[remainder_hash] = remainder
                    #!!!send_multiple with is_fin flag set!!!
                elif len(block_payload) <= BLOCK_SIZE and packet.is_fin:
                    hasch = utils.get_hash(block_payload)
                    self.hashes[hasch] = block_payload
                    #!!!send_multiple with is_fin flag set!!!
                elif len(block_payload) >= BLOCK_SIZE:
                    remainder = block_payload[BLOCK_SIZE:]
                    hasch = utils.get_hash(block_payload[:BLOCK_SIZE])
                    self.hashes[hasch] = block_payload[:BLOCK_SIZE]
                    #!!!send_multiple!!!
                    #if there's a remainder then update block_payload
                    if len(remainder) > 0:
                        self.buffers[packet_key] = remainder
                #self.send(packet, self.address_to_port[packet.dest]) for reference
            else:
                #get block payload from hashes
                block_payload = self.hashes[packet.payload]
                #!!!send_multiple(block_payload, self.address_to_port[packet.dest], packet.is_fin)!!!
        #Case 2
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.

            #add packet to buffers
            packet_key = (packet.src, packet.dest)
            if packet_key not in self.buffers.keys():
                self.buffers[packet_key] = packet.payload
            else:
                block_payload = self.buffers[packet_key]
                block_payload += packet.payload
                self.buffers[packet_key] = block_payload

            #add block to hashes
            block_payload = self.buffers[packet_key]
            if packet.is_fin:
                if block_payload.size <= BLOCK_SIZE:
                    #check if in hashes
                    #if so then send hash packet with is_fin flag set
                    #otherwise send multiple with is_fin flag set
                else: # block_payload.size > BLOCK_SIZE
                    #split remainder and the main
                    #if main in hashes then send hash packet
                    #otherwise send multiple
                    #if remainder in hashes then send hash packet with is_fin flag set
                    #otherwise send multiple with is_fin flag set
            elif block_payload.size >= BLOCK_SIZE:
                remainder = block_payload[BLOCK_SIZE:]
                hasch = utils.get_hash(block_payload[:BLOCK_SIZE])
                if hasch not in self.hashes.keys():
                    self.hashes[hasch] = block_payload[:BLOCK_SIZE]
                    send_multiple(hasch)
                else:
                    #send optimal packet
                    optimal_packet = tcp_packet.Packet(
                        packet_key[0],
                        packet_key[1],
                        False,
                        False,
                        hasch,
                        hasch.size)
                    self.send(optimal_packet, self.wan_port)

                #if there's a remainder then update block_payload
                if remainder.size >= 1:
                    self.buffers[packet_key] = remainder

                #send regular packet
                #self.send(packet, self.wan_port)
