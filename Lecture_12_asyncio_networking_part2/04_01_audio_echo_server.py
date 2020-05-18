import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import argparse
import sys
from typing import Callable, Coroutine

import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format='%(name)8s %(levelname)8s %(message)s')
logger = logging.getLogger("Main")

# Numpy datatype corresponding to the data type of the audio data (little-endian 16-bit signed integer).
sample_data_type = np.dtype(np.int16).newbyteorder('<')

# Sample rate of the audio signal.
sample_rate = 16000

# Number of samples in a single audio frame.
frame_size = 512


async def run():
    """
    Run a TCP server that reads audio frames and sends them back.
    """

    parser = argparse.ArgumentParser(description="Start the TCP audio server.")
    parser.add_argument('--listen', type=str, default="0.0.0.0",
                        help="Listen address of the server.")
    parser.add_argument('--port', type=int, required=True,
                        help="TCP port.")

    args = parser.parse_args()

    # Get the server address and port from the command line arguments.
    listen_addr = args.listen
    server_port = args.port

    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")

        try:
            while True:
                # Read data from the TCP stream.
                data = await reader.readexactly(frame_size * 2)
                writer.write(data)
                await writer.drain()

        except Exception as e:
            # Handle exceptions.
            # For instance if the connection is interrupted.
            print("Exception:", e)
        finally:
            print("Connection closed!")

    print(f"Starting server on {listen_addr}:{server_port}")
    # Create server instance.
    server = await asyncio.start_server(
        handle_connection,  # This function will be called for every new connection.
        listen_addr,
        server_port
    )

    # Run the server.
    async with server:  # `server` is an asynchronous context manager.
        await server.serve_forever()

    print("Server terminated.")


if __name__ == "__main__":
    asyncio.run(run())
