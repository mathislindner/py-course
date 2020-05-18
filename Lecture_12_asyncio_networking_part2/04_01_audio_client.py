import asyncio
from concurrent.futures import ThreadPoolExecutor
import pyaudio
import numpy as np
import argparse
import sys
from typing import Callable, Coroutine

import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format='%(name)8s %(levelname)8s %(message)s')
logger = logging.getLogger("Main")

# PyAudio singleton.
audio: pyaudio.PyAudio = pyaudio.PyAudio()

# Audio format to be used.
audio_format = pyaudio.paInt16

# Numpy datatype corresponding to the data type of the audio data (little-endian 16-bit signed integer).
sample_data_type = np.dtype(np.int16).newbyteorder('<')

# Sample rate of the audio signal.
sample_rate = 16000

# Number of samples in a single audio frame.
frame_size = 512

# Thread pool for running blocking tasks
# such as reading from the microphone and writing to the speakers and reading from stdin.
thread_pool = ThreadPoolExecutor()


async def run_mic(send_packet: Callable[[bytes], Coroutine]):
    """
    Read audio data from the microphone and send it to the server.
    The data is sent using the `send_packet` async function.
    """
    logger.debug("Start microphone task.")
    # Open audio input stream.
    stream_in = audio.open(format=audio_format,
                           channels=1,
                           rate=sample_rate,
                           input=True,
                           frames_per_buffer=frame_size)

    try:
        logger.debug('Start recording and sending audio.')

        while True:
            await asyncio.sleep(0)

            def read_from_mic() -> np.ndarray:
                """
                Read one audio frame from the microphone and convert it to a numpy array.
                This is a blocking function. Therefore it must be run from another thread.
                """
                # Read a frame from the microphone.
                frame = stream_in.read(frame_size)
                # Convert bytes into ndarray.
                signal = np.frombuffer(frame, dtype=sample_data_type)
                return signal

            # Read from mic in other thread.
            loop = asyncio.get_event_loop()
            frame = await loop.run_in_executor(thread_pool, read_from_mic)
            assert isinstance(frame, np.ndarray), "Frame must be an np.ndarray."

            # Write this frame as bytes to the server.
            await send_packet(frame.tobytes())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Microphone task interrupted: {}".format(e))

    logger.debug('Microphone task ended.')


async def run_speaker(audio_buffer: asyncio.Queue):
    """
    Read audio frames from the queue and write them to the audio output.
    The audio frames should be numpy arrays.
    """
    logger.debug("Start speaker task.")

    # Open audio output stream (to speaker).
    stream_out = audio.open(format=audio_format,
                            channels=1, # Mono, only one channel.
                            rate=sample_rate,
                            output=True,
                            frames_per_buffer=frame_size)

    async def speaker_task():
        silence = np.zeros(frame_size, dtype=sample_data_type)

        while True:

            if audio_buffer.qsize() > 0:
                # If there is something in the buffer, then get it.
                frame = audio_buffer.get_nowait()
                assert isinstance(frame, np.ndarray), "Frame should be a Numpy array."
            else:
                # No data has arrived yet. Send a zero-signal to the speaker.
                frame = silence

            def write_to_speaker():
                """
                Write the frame to the output audio stream.
                `stream_out.write` is blocking and therefore has to be run in a separate thread.
                """
                stream_out.write(frame.astype(np.int16), len(frame))

            loop = asyncio.get_event_loop()
            # Send data to the speaker.
            await loop.run_in_executor(thread_pool, write_to_speaker)

    _speaker_task = asyncio.create_task(speaker_task())

    await _speaker_task


async def run():
    parser = argparse.ArgumentParser(description="Create TCP connection to a server.")
    parser.add_argument('--server', type=str, required=True,
                        help="Hostname or address of the server.")
    parser.add_argument('--port', type=int, required=True,
                        help="TCP port.")

    args = parser.parse_args()

    # Get the server address and port from the command line arguments.
    server_addr = args.server
    server_port = args.port

    # Create a queue that is used to communicate to the speaker task.
    audio_queue_to_speaker = asyncio.Queue()

    # Open a TCP connection to the audio server.
    reader, writer = await asyncio.open_connection(
        server_addr, server_port)

    async def run_reader(reader: asyncio.StreamReader):
        """
        Read audio frames from the server and forward them to the speaker task.
        """
        while not reader.at_eof():
            # Read the raw audio frame bytes from the server.
            frame_bytes = await reader.readexactly(frame_size * 2)  # A 16-bit sample consists of 2 bytes.
            # Convert frame to a numpy array.
            frame = np.frombuffer(frame_bytes, dtype=sample_data_type).astype(np.int)
            # Send the frame to the speaker task via the queue.
            audio_queue_to_speaker.put_nowait(frame)
        print("Reader task terminated.")

    async def send_packet(data: bytes):
        """
        Helper function to send bytes to the server.
        :param data:
        :return:
        """
        writer.write(data)
        await writer.drain()

    # Start the reader task.
    reader_task = asyncio.create_task(run_reader(reader))

    # Start the microphone task and tell it which function to use for sending data to the server.
    mic_task = asyncio.create_task(run_mic(send_packet))

    # Start the speaker task.
    speaker_task = asyncio.create_task(run_speaker(audio_queue_to_speaker))

    # Wait until the reader task terminates.
    await reader_task

    # Cancel the other tasks.
    mic_task.cancel()
    speaker_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())