import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import argparse
import sys
from typing import Any, Callable, Coroutine, Dict, Tuple
import itertools
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


class AudioMixer:
    """
    The AudioMixer reads audio signals from the clients via queues.
    It mixes all the signals and sends the result back via queues.
    """

    def __init__(self):
        # Create a counter to generate unique client IDs.
        self.next_client_id = itertools.count(start=1)
        # Store the audio queues to and from the clients.
        self.audio_queues: Dict[int, Tuple[asyncio.Queue, asyncio.Queue]] = dict()

    def register_client(self) -> Tuple[int, Tuple[asyncio.Queue, asyncio.Queue]]:
        """
        Create a new ID and new audio queues for this client.
        The queues are used to forward audio frames to the mixer and
        then from the mixer back to the client.

        Returns a tuple like (id, (audio queue 'from client to mixer', audio queue 'from mixer to client')).
        """
        from_client = asyncio.Queue(maxsize=8)
        to_client = asyncio.Queue(maxsize=8)

        # Generate a new client ID.
        client_id = next(self.next_client_id)

        # Store the queues.
        self.audio_queues[client_id] = (from_client, to_client)

        return client_id, (from_client, to_client)

    def remove_client(self, id: int):
        """
        Remove the audio queues of this client.
        """
        del self.audio_queues[id]

    async def run_mixer(self):

        # Generate a frame of silence.
        silence = np.zeros(frame_size, dtype=sample_data_type)

        # Compute the delay between frames.
        frame_duration = frame_size / sample_rate

        # Time of the next audio frame.
        next_frame_time = time.time()

        while True:

            # Make sure this loop is executed as periodically as possible.
            slack = next_frame_time - time.time()
            if slack > 0:
                # Have to wait.
                await asyncio.sleep(slack)
            next_frame_time += frame_duration

            # Get the most recent audio frame for every client.
            frames = dict()
            # Compute the sum of all available frames.
            for id, (q_in, _) in self.audio_queues.items():
                if not q_in.empty():
                    frame = q_in.get_nowait()
                else:
                    frame = silence.copy()
                frames[id] = frame

            sum_of_all_frames = sum(frames.values(), silence)

            # Iterate over all output audio queues.
            for id, (_, q_out) in self.audio_queues.items():
                # STUDENT TASK: Send back the sum of the frames
                # to the clients by using the queue `q_out`.
                # The simplest solution would be:
                # `q_out.put_nowait(sum_of_all_frames)`
                # However there are two more requirements.
                # 1) First check if `q_out` is full. In this case drop the oldest frame in `q_out` before
                # putting the new one.
                # 2) Users don't want to hear themselves! Subtract the right frame from the sum
                # before sending the frame.
                if(q_out.full()):
                    q_out.get_nowait()
                client_out_frame = sum_of_all_frames.substract(frames[id]) #idk the right semantic
                q_out.put_nowait(client_out_frame)


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

    mixer = AudioMixer()

    # Run the mixer in the background.
    asyncio.create_task(mixer.run_mixer())

    async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        This is called for every new TCP connection.
        """
        print("New connection!")
        
        # STUDENT TASK: Register the client at the audio mixer.
        # Study the class AudioMixer!
        # Need something like:
        # client_id, (to_mixer, from_mixer) = ...
        client_id, (to_mix, to_client) = mixer.register_client()
        
        try:

            async def reader_task():
                """
                Read audio frames from the client and pass them to the audio mixer.
                """
                while True:

                    # Read data from the TCP stream.
                    data = await reader.readexactly(frame_size * 2)

                    # Deserialize the data to a Numpy array.
                    frame = np.frombuffer(data, dtype=sample_data_type)

                    # STUDENT TASK: Pass the frame to the mixer using the right queue.
                    # First check if the queue is full.
                    # If the queue is full, drop the oldest frame from the queue before
                    # putting the new one into the queue.
                    # Pass the frame to the mixer via the queue.
                    if (to_mix.full()):
                        to_mix_get.nowait() #I feel like it s not going to affect the queue in the mixer but just the one in the handle_connection function (maybe access with sth like that instead ?mixer.audioqueues[client_id])
                    to_mix.put(frame)

            async def writer_task():
                """
                Get audio frames from the audio mixer queue and write them to the client.
                """

                while True:
                    # STUDENT TASK: Get an audio frame from the mixer, convert it to bytes
                    # and write it to the client.
                    this_frame = to_client.get()
                    converted = np.tobuffer(this_frame, dtype=sample_data_type)
                    await writer.write(converted) 

            # Start reader and writer tasks.
            _reader_task = asyncio.create_task(reader_task())
            _writer_task = asyncio.create_task(writer_task())

            # Wait for the reader task to be finished.
            await _reader_task

            # Cancel the writer task.
            _writer_task.cancel()

        except Exception as e:
            # Handle exceptions.
            # For instance if the connection is interrupted.
            print("Exception:", e)
        finally:
            print("Connection closed!")
            # STUDENT TASK: Remove the client queues from the mixer.
            # Hint: Use the ID obtained while registering the client.
            audio_queues.pop(client_id)
            

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
