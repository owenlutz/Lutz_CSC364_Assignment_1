import socket
import time
import os
from threading import Thread

#config so copy paste for rest of routers
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8003
FORWARDING_TABLE_PATH = "router_3_table.csv"

OUTPUT_DIR = "./output"
RECEIVED_LOG = os.path.join(OUTPUT_DIR, "received_by_router_3.txt")
SENT_LOG = os.path.join(OUTPUT_DIR, "sent_by_router_3.txt")
DISCARDED_LOG = os.path.join(OUTPUT_DIR, "discarded_by_router_3.txt")
OUT_LOG = os.path.join(OUTPUT_DIR, "out_router_3.txt")
OUTPUT_TTL0_LOG = OUT_LOG

# same from router1.py
def create_socket(host, port, message: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))
            print(f"[router_2] Connected to server at {host}:{port}")
            client_socket.sendall(message.encode("utf-8"))
        except ConnectionRefusedError:
            print("[router_2] Connection refused. Make sure the next router is running.")
        except Exception as e:
            print(f"[router_2] An error occurred: {e}")
        print("[router_2] Connection closed.")


def read_csv(path):
    data = []
    with open(path, "r") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            row_elements = stripped_line.split(",")
            data.append(row_elements)
    return data


def ip_to_int(ip: str) -> int:
    parts = ip.strip().split(".")
    n = 0
    for p in parts:
        n = (n << 8) | int(p)
    return n


def find_default_gateway(table):
    for row in table:
        if ip_to_int(row[0]) == 0:
            return row[3].strip()  # may be "127.0.0.1" OR a port
    raise LookupError("No default gateway found in forwarding table.")


def find_hop(packet, forwarding_table):
    dest_ip_int = ip_to_int(packet[1])
    best_next = None
    best_prefix = -1

    for row in forwarding_table:
        network_ip = ip_to_int(row[0])
        netmask = ip_to_int(row[1])
        next_hop = row[3].strip()  # may be "127.0.0.1" OR a port string

        if (dest_ip_int & netmask) == (network_ip & netmask):
            prefix = bin(netmask).count("1")
            if prefix > best_prefix:
                best_prefix = prefix
                best_next = next_hop

    return best_next if best_next is not None else find_default_gateway(forwarding_table)


#server router logic

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def log_line(path, line: str):
    ensure_output_dir()
    with open(path, "a") as f:
        f.write(line + "\n")


def handle_client(client_socket, client_address, forwarding_array):
    print(f"[router_2] Accepted connection from {client_address}")
    try:
        data = client_socket.recv(4096)
        if not data:
            return

        message = data.decode("utf-8").strip()
        print(f"[router_2] recv {message}")

        # Parse incoming packet (CSV line -> list)
        row = message.split(",")

        # Log received (as seen/processed by router 2)
        log_line(RECEIVED_LOG, ",".join(map(str, row)))

        # Decrement TTL
        row[3] = int(row[3]) - 1

        # Determine next hop
        next_hop = find_hop(row, forwarding_array)
        is_final_router = (str(next_hop).strip() == "127.0.0.1")

        # TTL expired
        if row[3] <= 0:
            if is_final_router:
                print(f"[router_2] Packet {row} delivered at final router (TTL=0)")
                log_line(OUTPUT_TTL0_LOG, ",".join(map(str, row)))
            else:
                print(f"[router_2] Packet {row} dropped due to TTL=0")
                log_line(DISCARDED_LOG, ",".join(map(str, row)))

            client_socket.sendall(b"success from router 2")
            return

        # Final hop reached with TTL still > 0
        if is_final_router:
            print(f"[router_2] Packet {row} delivered at final router")
            log_line(OUT_LOG, ",".join(map(str, row)))
            client_socket.sendall(b"success from router 2")
            return

        # Forward packet to next router
        forward_message = ",".join(map(str, row))
        log_line(SENT_LOG, forward_message)

        port = int(str(next_hop).strip())
        create_socket(LISTEN_HOST, port, forward_message)

        # Optional small delay to reduce burstiness (matches router_1 style)
        time.sleep(1)

        client_socket.sendall(b"success from router 2")

    except socket.error as e:
        print(f"[router_2] Socket error: {e}")
    except Exception as e:
        print(f"[router_2] Error handling client: {e}")
    finally:
        client_socket.close()


def router_2_main():
    ensure_output_dir()
    forwarding_array = read_csv(FORWARDING_TABLE_PATH)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = (LISTEN_HOST, LISTEN_PORT)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print(f"[router_2] server is listening on {server_address}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = Thread(
            target=handle_client,
            args=(client_socket, client_address, forwarding_array),
            daemon=True,
        )
        client_thread.start()


if __name__ == "__main__":
    router_2_main()
