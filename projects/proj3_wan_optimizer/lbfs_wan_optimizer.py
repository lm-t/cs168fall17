import wan_optimizer
import utils
from tcp_packet import Packet

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into variable-sized
    blocks based on the contents of the file.

    This WAN optimizer should implement part 2 of project 4.
    """

    # The string of bits to compare the lower order 13 bits of hash to
    GLOBAL_MATCH_BITSTRING = '0111011001010'

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
        functionality described in part 2.  You are welcome to implement private
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
            while len(block_payload) > utils.MAX_PACKET_SIZE:
                pckt = Packet(
                        packet_key[0],
                        packet_key[1],
                        True,
                        False,
                        block_payload[:utils.MAX_PACKET_SIZE])
                block_payload = block_payload[utils.MAX_PACKET_SIZE:]
                self.send(pckt, port)
            pckt = Packet(
                    packet_key[0],
                    packet_key[1],
                    True,
                    is_fin,
                    block_payload)
            self.send(pckt, port)

        packet_key = (packet.src, packet.dest)
        if packet.src in self.address_to_port and packet.dest in self.address_to_port:
            # The packet is from a client connected to this middlebox and
            # the packet is destined to a client connected to this middlebox
            self.send(packet, self.address_to_port[packet.dest])
        #Case 2
        elif packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            if packet.is_raw_data:
                #add packet payload to block payload
                if packet_key not in self.buffers.keys():
                    self.buffers[packet_key] = packet.payload
                else:
                    block_payload = self.buffers[packet_key]
                    block_payload += packet.payload
                    self.buffers[packet_key] = block_payload
                #break blocks using delimiter
                buffer_size = len(self.buffers[packet_key])
                place_holder = 0
                while buffer_size >= 48:
                    window = self.buffers[packet_key][place_holder:48 + place_holder]
                    window_hash = utils.get_hash(window)
                    low_order_13 = utils.get_last_n_bits(window_hash, 13)
                    if low_order_13 == WanOptimizer.GLOBAL_MATCH_BITSTRING:
                        block_payload = self.buffers[packet_key][:place_holder + 48]
                        hasch = utils.get_hash(block_payload)
                        self.hashes[hasch] = block_payload
                        #send_multiple with is_fin
                        send_multiple(block_payload, self.address_to_port[packet.dest], False)
                        #clear buffer
                        self.buffers[packet_key] = self.buffers[packet_key][place_holder + 48:]
                        place_holder += 48
                        buffer_size -= 48
                    else:
                        #slide window by 1
                        place_holder += 1
                        buffer_size -= 1
                if packet.is_fin:
                    hasch = utils.get_hash(self.buffers[packet_key])
                    self.hashes[hasch] = self.buffers[packet_key]
                    send_multiple(self.buffers[packet_key], self.address_to_port[packet.dest], packet.is_fin)
                    #clear buffer
                    self.buffers[packet_key] = ''
            else:
                #get block payload from hashes
                block_payload = self.hashes[packet.payload]
                send_multiple(block_payload, self.address_to_port[packet.dest], packet.is_fin)
        #Case 3
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            # self.send(packet, self.wan_port)

            #add packet payload to block payload
            if packet_key not in self.buffers.keys():
                self.buffers[packet_key] = packet.payload
            else:
                block_payload = self.buffers[packet_key]
                block_payload += packet.payload
                self.buffers[packet_key] = block_payload
            #get block from buffer
            buffer_size = len(self.buffers[packet_key])
            place_holder = 0
            while buffer_size >= 48:
                window = self.buffers[packet_key][place_holder:48 + place_holder]
                window_hash = utils.get_hash(window)
                low_order_13 = utils.get_last_n_bits(window_hash, 13)
                if low_order_13 == WanOptimizer.GLOBAL_MATCH_BITSTRING:
                    block_payload = self.buffers[packet_key][:place_holder + 48]
                    hasch = utils.get_hash(block_payload)
                    if hasch in self.hashes.keys():
                        send_with_hash(hasch, packet.is_fin)
                    else:
                        self.hashes[hasch] = block_payload
                        #send_multiple
                        send_multiple(block_payload, self.wan_port, False)
                    #clear buffer
                    self.buffers[packet_key] = self.buffers[packet_key][place_holder + 48:]
                    place_holder += 48
                    buffer_size -= 48
                else:
                    #slide window by 1
                    place_holder += 1
                    buffer_size -= 1
            if packet.is_fin:
                hasch = utils.get_hash(self.buffers[packet_key])
                #send packet
                if hasch in self.hashes.keys():
                    send_with_hash(hasch, packet.is_fin)
                else:
                    self.hashes[hasch] = self.buffers[packet_key]
                    #send_multiple with is_fin
                    send_multiple(self.buffers[packet_key], self.wan_port, packet.is_fin)
                #clear buffer
                self.buffers[packet_key] = ''
