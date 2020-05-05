import socket

# Create a TCP/IP server socket.
# AF = Address Family
# INET = IPv4
# SOCK_STREAM = TCP
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Make sure to be able to re-open the socket if it is still busy with
# an old connection.
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Listen to connections coming from 'localhost' on port 12345.
serversocket.bind(('localhost', 12345))
serversocket.listen()

while True:
    print("Wait for client to connect...")
    (sock, address) = serversocket.accept()
    print("Incoming connection from", address)
    
    sock.sendall(b"Hello! I'm the server!\n")
    
    input_data = sock.recv(4096) # Receive at most 4096 bytes.
    print("Received data:", input_data)
    
    # Notice that only one client connection will be handled at a time.
    # Parallelism would have to be implemented using 'threads'.

serversocket.close()
