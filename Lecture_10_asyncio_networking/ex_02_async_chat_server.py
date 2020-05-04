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
    
    # STUDENT TASK: Create a dict 'rooms' which holds for every room name a set of stream writers.
    ...
    
    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")
  
        # This is the name of the current chat room for this client.
        room_name = None

        try:
            # Write a hello message to the client.
            writer.write(b"Hello! You did not yet join a room.\n")
            writer.write(b"To join a room type: `/join ROOMNAME`\n")
            
            # Process incoming lines.
            while not reader.at_eof():
                # Read a line from the TCP stream.
                line_bytes = await reader.readline()
                print("Got a line:", line_bytes.decode('utf-8'))
                
                # Test if the line is a 'join' command.
                if line_bytes.startswith(b"/join "):
                    # Handle the command.
                    if room_name is not None:
                        # STUDENT TASK: Leave the old room.
                        ...
                        
                    # Join the new room.
                    # STUDENT TASK: Find out the room name. Make sure to strip away a trailing newline!
                    room_name = ...
                    # STUDENT TASK: Create an empty room if there is no room yet with this name.
                    # Then add the stream writer to this room such that
                    # other clients can send messages to this client.
                    ...
                    
                    writer.write(b"You joined the room '"+room_name+b"'\n")
                else:
                    # Line was not a command.
                    
                    # STUDENT TASK: Send the line to all other connected clients in this room.
                    if room_name in rooms:
                        ...
                    
        except Exception as e:
            print("Exception:", e)
        finally:
            
            if room_name is not None:
                # STUDENT TASK: Remove the stream writer from the room.
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
