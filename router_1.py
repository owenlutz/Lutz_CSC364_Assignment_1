import socket
import sys
import time
import os
import glob

# Helper Functions
# note - socket autoclosed by using with, as with manages context
# The purpose of this function is to set up a socket connection 
def create_socket(host, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket: 
        try: 
            client_socket.connect((host, port))
            print(f"Connected to server at {host}:{port}")
            client_socket.sendall(message.encode('utf-8'))

        except ConnectionRefusedError:
            print("Connection refused. Make sure the server is running.")
        except Exception as e:
            print(f"An error occurred: {e}")

        print("Connection closed.")


def router_1_main(forwarding_table, packets):
    packet_array = read_csv(packets)
    forwarding_array = read_csv(forwarding_table)

    for row in packet_array:
        # log packet as received by router 1 (originating router)
        with open('./output/received_by_router_1.txt', 'a') as recv_file:
            recv_file.write(','.join(map(str, row)) + '\n')

        # decrement TTL
        row[3] = int(row[3]) - 1

        # determine next hop (string: "127.0.0.1" or port)
        next_hop = find_hop(row, forwarding_array)
        is_final_router = (str(next_hop).strip() == "127.0.0.1")

        # TTL expired
        if row[3] <= 0:
            if is_final_router:
                print(f"Packet {row} delivered at final router (TTL=0)")
                with open('./output/output_packets.txt', 'a') as out_file:
                    out_file.write(','.join(map(str, row)) + '\n')
            else:
                print(f"Packet {row} dropped due to TTL=0")
                with open('./output/discarded_by_router_1.txt', 'a') as drop_file:
                    drop_file.write(','.join(map(str, row)) + '\n')
            continue

        # final hop reached with TTL still > 0
        if is_final_router:
            print(f"Packet {row} delivered at final router")
            with open('./output/out_router_1.txt', 'a') as out_file:
                out_file.write(','.join(map(str, row)) + '\n')
            continue

        # forward packet to next router
        message = ','.join(map(str, row))

        with open('./output/sent_by_router_1.txt', 'a') as sent_file:
            sent_file.write(message + '\n')

        port = int(next_hop)
        create_socket("127.0.0.1", port, message)
        time.sleep(1)





def find_hop(packet, forwarding_table):
    dest_ip_int = ip_to_int(packet[1])
    best_next = None
    best_prefix = -1

    for row in forwarding_table:
        network_ip = ip_to_int(row[0])
        netmask = ip_to_int(row[1])
        next_hop = row[3].strip() 

        if (dest_ip_int & netmask) == (network_ip & netmask):
            prefix = bin(netmask).count("1")
            if prefix > best_prefix:
                best_prefix = prefix
                best_next = next_hop

    return best_next if best_next is not None else find_default_gateway(forwarding_table)

        

# The purpose of this function is to read in a CSV file.
def read_csv(path):
    data = []
    with open(path, 'r') as file: 
        for line in file:
            stripped_line = line.strip() 
            row_elements = stripped_line.split(',') 
            data.append(row_elements)

    return data


# The purpose of this function is to find the default port
# when no match is found in the forwarding table for a packet's destination IP.
def find_default_gateway(table):
    for row in table:
        if ip_to_int(row[0]) == 0:
            return row[3].strip()   # may be "127.0.0.1" OR a port
    raise LookupError("No default gateway found in forwarding table.")

def ip_to_int(ip: str) -> int:
    parts = ip.strip().split(".")
    n = 0
    for p in parts:
        n = (n << 8) | int(p)
    return n


# The purpose of this function is to perform a bitwise NOT on an unsigned integer.
def bit_not(n, numbits=32):
    return (1 << numbits) - 1 - n

files = glob.glob('./output/*')
for f in files:
    os.remove(f)
router_1_main('router_1_table.csv','packets.csv')


