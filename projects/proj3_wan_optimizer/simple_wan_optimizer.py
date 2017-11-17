import wan_optimizer
import utils
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
        self.hashes = {} #key:value -> hash:block
        self.buffers = {} #key:value -> (source, destination):block
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
        def send_with_hash(hasch, is_fin):
            #send hash packet
            is_raw_data = False
            hash_packet = Packet(
                packet_key[0],
                packet_key[1],
                is_raw_data,
                is_fin,
                hasch)
            self.send(hash_packet, self.wan_port)
        def send_multiple(block_payload, port, is_fin):
            packets = []
            for i in range(0, len(block_payload), utils.MAX_PACKET_SIZE):
                pload = block_payload[i: i + utils.MAX_PACKET_SIZE]
                pckt = Packet(
                    packet_key[0],
                    packet_key[1],
                    True,
                    False,
                    pload)
                self.send(pckt, port)
            if is_fin:
                pckt = Packet(
                    packet_key[0],
                    packet_key[1],
                    True,
                    True,
                    '')
                self.send(pckt, port)

        packet_key = (packet.src, packet.dest)
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
                # packet_key = (packet.src, packet.dest)
                #add packet payload to block payload
                if packet_key not in self.buffers.keys():
                    self.buffers[packet_key] = packet.payload
                else:
                    block_payload = self.buffers[packet_key]
                    block_payload += packet.payload
                    self.buffers[packet_key] = block_payload
                #if buffer payload is full or is_fin
                block_payload = self.buffers[packet_key]
                if len(block_payload) > WanOptimizer.BLOCK_SIZE and packet.is_fin:
                    remainder = block_payload[WanOptimizer.BLOCK_SIZE:]
                    #add block payload to hashes
                    hasch = utils.get_hash(block_payload[:WanOptimizer.BLOCK_SIZE])
                    self.hashes[hasch] = block_payload[:WanOptimizer.BLOCK_SIZE]
                    #add remainder payload to hashes
                    remainder_hash = utils.get_hash(remainder)
                    self.hashes[remainder_hash] = remainder
                    #clear buffer
                    self.buffers[packet_key] = ''
                elif len(block_payload) == WanOptimizer.BLOCK_SIZE or packet.is_fin:
                    hasch = utils.get_hash(block_payload)
                    self.hashes[hasch] = block_payload
                    #clear buffer
                    self.buffers[packet_key] = ''
                elif len(block_payload) >= WanOptimizer.BLOCK_SIZE:
                    remainder = block_payload[WanOptimizer.BLOCK_SIZE:]
                    hasch = utils.get_hash(block_payload[:WanOptimizer.BLOCK_SIZE])
                    self.hashes[hasch] = block_payload[:WanOptimizer.BLOCK_SIZE]
                    #clear buffer
                    self.buffers[packet_key] = ''
                    #if there's a remainder then update block_payload
                    if len(remainder) > 0:
                        self.buffers[packet_key] = remainder
                self.send(packet, self.address_to_port[packet.dest])
            else:
                #get block payload from hashes
                block_payload = self.hashes[packet.payload]
                send_multiple(block_payload, self.address_to_port[packet.dest], packet.is_fin)
        #Case 2
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.

            #add packet to buffers
            # packet_key = (packet.src, packet.dest)
            if packet_key not in self.buffers.keys():
                self.buffers[packet_key] = packet.payload
            else:
                block_payload = self.buffers[packet_key]
                block_payload += packet.payload
                self.buffers[packet_key] = block_payload

            #send either hash packet or regular packets depending on cases
            block_payload = self.buffers[packet_key]
            if len(block_payload) > WanOptimizer.BLOCK_SIZE and packet.is_fin:
                remainder = block_payload[WanOptimizer.BLOCK_SIZE:]
                #send hash packet or multiple packets
                hasch = utils.get_hash(block_payload[:WanOptimizer.BLOCK_SIZE])
                if hasch in self.hashes.keys():
                    ###send hash packet
                    send_with_hash(hasch, False)
                else:
                    self.hashes[hasch] = block_payload[:WanOptimizer.BLOCK_SIZE]
                    send_multiple(block_payload, self.wan_port, False)
                #send remainder_payload
                remainder_hash = utils.get_hash(remainder)
                if remainder_hash in self.hashes.keys():
                    ###send remainder hash packet with is_fin flag set
                    send_with_hash(remainder_hash, packet.is_fin)
                else:
                    self.hashes[remainder_hash] = remainder
                    send_multiple(remainder, self.wan_port, packet.is_fin)
            elif len(block_payload) == WanOptimizer.BLOCK_SIZE or packet.is_fin:
                #send hash packet or multiple packets
                hasch = utils.get_hash(block_payload)
                if hasch in self.hashes.keys():
                    ###send hash packet with is_fin flag set
                    send_with_hash(hasch, packet.is_fin)
                else:
                    self.hashes[hasch] = block_payload
                    send_multiple(block_payload, self.wan_port, packet.is_fin)
                #clear buffer
                self.buffers[packet_key] = ''
            elif len(block_payload) >= WanOptimizer.BLOCK_SIZE:
                remainder = block_payload[WanOptimizer.BLOCK_SIZE:]
                hasch = utils.get_hash(block_payload[:WanOptimizer.BLOCK_SIZE])
                if hasch in self.hashes.keys():
                    ###send hash packet
                    send_with_hash(hasch, packet.is_fin)
                else:
                    self.hashes[hasch] = block_payload[:WanOptimizer.BLOCK_SIZE]
                    send_multiple(block_payload[:WanOptimizer.BLOCK_SIZE], self.wan_port, packet.is_fin)
                #update buffer
                self.buffers[packet_key] = ''
                #if there's a remainder then update block_payload
                if len(remainder) > 0:
                    self.buffers[packet_key] = remainder
