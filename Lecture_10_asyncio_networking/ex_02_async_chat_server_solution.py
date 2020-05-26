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
    
    # STUDENT TASK: Create a dict which holds for every room name a set of stream writers.
    # START PART OF SOLUTION
    rooms = dict()
    # END PART OF SOLUTION
    
    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")
        
        # STUDENT TASK: Register the stream writer such that it can be accessed
        # from other sessions. (store it in the set)
        # START PART OF SOLUTION
        # all_stream_writers.add(writer) # Old code
        # END PART OF SOLUTION

        # This is the name of the current chat room for this client.
        room_name = None

        try:
            # Write hello message to the client.
            writer.write(b"Hello! You did not yet join a room.\n")
            writer.write(b"To join a room type: `/join ROOMNAME`\n")
            
            # Process incoming lines.
            while not reader.at_eof():
                # Read a line from the TCP stream.
                line_bytes = await reader.readline()
                print("Got a line:", line_bytes.decode('utf-8'))
                
                # Test if the line was a command.
                if line_bytes.startswith(b"/join "):
                    # Handle the command.
                    if room_name is not None:
                        # Leave the old room.
                        rooms[room_name].remove(writer)
                    # Join the room.
                    room_name = line_bytes[6:-1] # Strip away the '/join ' and the newline.
                    rooms.setdefault(room_name, set()).add(writer)
                    writer.write(b"You joined the room '"+room_name+b"'\n")
                else:
                    # Line was not a command.
                    
                    # Send the line to all other connected clients in this room.
                    if room_name in rooms:
                        for w in rooms[room_name]:
                            if w != writer: # Don't send back to the author.
                                w.write(line_bytes)
                    
        except Exception as e:
            print("Exception:", e)
        finally:
            
            # STUDENT TASK: Remove the stream writer from the room.
            # START PART OF SOLUTION
            if room_name is not None:
                rooms[room_name].remove(writer)
            # END PART OF SOLUTION
            
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
