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

    def __init__(self):
        self.next_client_id = itertools.count(start=1)  # Counter to generate unique client IDs.
        # Store the audio queues to and from the clients.
        self.audio_queues: Dict[int, Tuple[asyncio.Queue, asyncio.Queue]] = dict()
        # Flag used to notify the running infinite loop to terminate.
        self.is_closed = False

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

    def close(self):
        """
        Terminate the task `run_mixer()`.
        This shall be called once all clients left the room.
        """
        self.is_closed = True

    async def run_mixer(self):

        # Generate a frame of silence.
        silence = np.zeros(frame_size, dtype=sample_data_type)

        # Compute the delay between frames.
        frame_duration = frame_size / sample_rate

        # Time of the next audio frame.
        next_frame_time = time.time()

        while not self.is_closed:

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

            for id, (_, q_out) in self.audio_queues.items():
                if q_out.full():
                    # Just drop the oldest frame if the queue is full.
                    q_out.get_nowait()
                frame = sum_of_all_frames - frames[id]
                q_out.put_nowait(frame)


# STUDENT TASK: Create a dict that will hold an AudioMixer object for every room.
# It shall be empty at the beginning. AudioMixers shall be created and added to the dict when needed.
# START SOLUTION
audio_mixers = dict()


# END SOLUTION


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

        # STUDENT TASK: Read the room name from the client.
        # START SOLUTION
        room_name = await reader.readline()
        room_name = room_name[:-1]  # Strip away the newline character.
        # END SOLUTION

        print(f"Client joins the room '{room_name.decode()}'.")

        # STUDENT TASK: Get an AudioMixer object for this room name.
        # Create a mixer object if none exists and store it in the dict.
        # The new mixer also has to be run with `asyncio.create_task(mixer.run_mixer())`.
        # START SOLUTION
        if room_name not in audio_mixers:
            mixer = AudioMixer()
            # Run the mixer in the background.
            asyncio.create_task(mixer.run_mixer())
            audio_mixers[room_name] = mixer

        mixer = audio_mixers[room_name]
        # END SOLUTION

        # Connect the client to the audio mixer.
        client_id, (to_mixer, from_mixer) = mixer.register_client()

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

                    # Pass the frame to the mixer via the queue.
                    if to_mixer.full():
                        # Drop the oldest packet if the queue is full.
                        to_mixer.get_nowait()
                    to_mixer.put_nowait(frame)

            async def writer_task():
                """
                Get audio frames from the audio mixer queue and write them to the client.
                """

                while True:
                    frame = await from_mixer.get()
                    writer.write(frame.tobytes())
                    await writer.drain()

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
            # Remove the client queues from the mixer.
            mixer.remove_client(client_id)

            # STUDENT TASK: Remove the audio mixer from the dict if there is no client registered in it anymore.
            # Also call `mixer.close()` to terminate the running audio mixing task.
            # Hint: Check if `mixer.audio_queues` is empty.
            # START SOLUTION
            if len(mixer.audio_queues) == 0:
                del audio_mixers[room_name]
                mixer.close()
            # END SOLUTION

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
