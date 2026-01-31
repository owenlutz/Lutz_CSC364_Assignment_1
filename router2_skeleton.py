import socket
import sys
import traceback
from threading import Thread

listening_port = 8002


def handle_client(client_socket, client_address,path):

    print(f"Accepted connection from {client_address}")
    try:
        data = client_socket.recv(1024)
        if data:
            print(f"recv {data.decode('utf-8')}")
            with open(path, 'r') as file:
                file.write(data.decode('utf-8'))

            response = "success from router 2"
            client_socket.sendall(response.encode('utf-8'))
    except socket.error as e:  
         print(f"Socket error: {e}")
    finally:
        client_socket.close()


def router_2_main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address =('localhost',listening_port)
    server_socket.bind(server_address)
    server_socket.listen(5)
    print(f"server is listening on {server_address}")

    while True: 
        client_socket, client_address = server_socket.accept()
        client_thread = Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()



router_2_main()