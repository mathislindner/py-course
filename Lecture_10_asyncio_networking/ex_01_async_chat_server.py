# Run a TCP chat server.

import asyncio

# Tell on which address and port to listen for connections.
server_addr = '0.0.0.0' # Allow other computers to connect.
server_port = 12345

async def main():
    """
    This TCP server reads data from a connection and sends the data
    to all other connections. This effectively creates a very simple
    chat room.
    """
    
    # STUDENT TASK: Create a set which contains the stream writers of all connections.
    # At the beginning this is empty.
    ...
    
    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")
        
        # STUDENT TASK: Register the stream writer such that it can be accessed
        # from other sessions. (Store it in the set.)
        ...

        try:
            while not reader.at_eof():
                # Read a line from the TCP stream.
                line_bytes = await reader.readline()
                print("Got a line:", line_bytes.decode('utf-8'))
                
                # STUDENT TASK: Send the line to all other connected clients instead of
                # answering with upper case.
                ...
                
                # Turn the line into upper case and send it back.
                writer.write(line_bytes.upper())
                    
        except Exception as e:
            print("Exception:", e)
        finally:
            
            # STUDENT TASK: Remove the stream writer from the set.
            ...
            
            print("Connection closed!")
            
    print(f"Starting server on {server_addr}:{server_port}")
    # Create server instance.
    server = await asyncio.start_server(
        handle_connection,
        server_addr,
        server_port
    )

    # Run the server.
    async with server:
        await server.serve_forever()
    
    print("Server terminated.")

asyncio.run(main()) 
