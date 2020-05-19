# Run a simple TCP server.
# It uses pickle.loads to deserialize data from the network
# and hence is vulnerable to execute arbitrary code.

import asyncio
import pickle

# Tell on which address and port to listen for connections.
server_addr = '127.0.0.1' # Better only allow local connections for your security.
server_port = 12345

async def main():
    """
    Run a TCP server that writes back all received data line by line.
    """
    
    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")

        try:
            # Read data from the TCP stream.
            data = await reader.read(4096)
            print("Got data:", data)
            
            # Deserialize the bytes.
            # The server expects to get a dict.
            obj = pickle.loads(data)
            
            if isinstance(obj, dict):
                print("Received a dict")
                print(obj)
                # Say thanks to the client.
                writer.write(b"Thanks for the dict!")
            else:
                print("Data has wrong type!")
                # Complain to the client.
                writer.write(b"Data has wrong type!")
        except Exception as e:
            # Handle exceptions.
            # For instance if the connection is interrupted.
            print("Exception:", e)
        finally:
            print("Connection closed!")
            
    print(f"Starting server on {server_addr}:{server_port}")
    # Create server instance.
    server = await asyncio.start_server(
        handle_connection, # This function will be called for every new connection.
        server_addr,
        server_port
    )

    # Run the server.
    async with server: # `server` is an asynchronous context manager.
        await server.serve_forever()
    
    print("Server terminated.")

asyncio.run(main()) 
