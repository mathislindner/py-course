import asyncio
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

# Create a thread pool with one worker for reading the user input.
thread_pool = ThreadPoolExecutor(max_workers=1)

# Create an 'ArgumentParser' to be able to set arguments from
# the command line.
parser = argparse.ArgumentParser(description="Create TCP connection to a server.")
parser.add_argument('--server', type=str, required=True,
    help="Hostname or address of the server.")
parser.add_argument('--port', type=int, required=True,
    help="TCP port.")

args = parser.parse_args()

# Get the server address and port from the command line arguments.
server_addr = args.server
server_port = args.port

async def run_client():
    print("Connect to server...")
    reader, writer = await asyncio.open_connection(
            server_addr, server_port)
    
    async def run_reader():
        while not reader.at_eof():
            line_bytes = await reader.readline()
            line = line_bytes.decode()
            line = line[:-1] # Strip away newline.
            print("server response >", line)
        print("Reader task terminated.")
        
        
    async def run_writer():
        print("Type something to write to the server:")
        
        while True:
            # Read a line from the user.
            # Because sys.stdin.readline is not `async` it will block 
            # the other tasks. Therefore this is best run on another thread.
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(thread_pool, sys.stdin.readline)
            # Convert the string into bytes.
            line_bytes = line.encode('utf-8')
            
            # Send the line to the server.
            writer.write(line_bytes)
            # Wait until everything is sent.
            await writer.drain()
            
    # Create a concurrent task that reads data from the server
    # and prints it on the standard output.
    reader_task = asyncio.create_task(run_reader())
    # Create another concurrent task that reads from the standard input
    # and writes the data to the server.
    writer_task = asyncio.create_task(run_writer())
    
    # Wait for the reader task to finish.
    await reader_task
    
    # Stop the writer task.
    writer_task.cancel()

asyncio.run(run_client())
