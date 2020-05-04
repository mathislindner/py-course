# Run a simple TCP server.

import asyncio

# Tell on which address and port to listen for connections.
server_addr = '127.0.0.1' # Use '0.0.0.0' to allow other computers to connect.
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
            # Process the incoming data line by line.
            while not reader.at_eof():
                # Read a line from the TCP stream.
                line_bytes = await reader.readline()
                print("Got a line:", line_bytes.decode('utf-8'))
                # Turn the line into upper case and send it back.
                writer.write(line_bytes.upper())
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
