from dataclasses import dataclass
import struct

import asyncio


@dataclass
class Message:
    choke: int = 0
    unchoke: int = 1
    interested: int = 2
    not_interested: int = 3
    have: int = 4
    bitfield: int = 5
    request: int = 6
    piece: int = 7
    cancel: int = 8
    port: int = 9

    async def handle_unchoke(self):
        ...

    async def handle_piece(self):
        ...

    def process_bitfield(self):
        ...

@dataclass
class DownloadState:
    """Keeps track of information on the download."""
    file_size: int
    filename: str
    piece_length: int
    pieces: bytes


@dataclass
class Peer:
    writer: asyncio.StreamWriter
    reader: asyncio.StreamReader
    is_choking: bool = False

    async def send_handshake(self, handshake: bytes) -> bytes | None:
        """Sends first ever message to peer."""
        self.writer.write(handshake)
        await self.writer.drain()
        return await self.read_handshake(handshake)

    async def read_handshake(self, handshake: bytes) -> bytes | None:
        """ Reads and validates peer's handshake.

        Each handshake should be 68 bytes long, and the info_hash
        of the response, which is 20 bytes long and is located at
        positions 28 to 48, should equal the client's info_hash.
        """
        response = await asyncio.wait_for(
            self.reader.readexactly(68), timeout=10
        )
        if response[28:48] == handshake[28:48]:
            return response
        return None

    async def send_interested(self):
        """ Informs peer that the client is interested in pieces they own.

            Peer's responds with one of the values in the "Message" dataclass.
        """
        message = struct.pack("!IB", 1, Message.interested)
        self.writer.write(message)
        await self.writer.drain()


def handle_dictionary_model(peers: dict) -> list[tuple[str, int]]:
    """Processes dictionaries with IP addresses of peers."""
    ips = []
    for peer in peers:
        ip = peer[b"ip"].decode()
        ips.append((ip, peer[b"port"]))
    return ips


def handle_binary_model(peers: bytes) -> list[tuple[str, int]]:
    """Processes byte-string with IP addresses of peers."""
    ips = []
    for chunk in (peers[i: i + 6] for i in range(0, len(peers), 6)):
        ip = '.'.join(map(str, chunk[:4]))
        if ip != "127.0.0.1":
            port = struct.unpack("!H", chunk[4:])[0]
            endpoint = (ip, port)
            ips.append(endpoint)
    return ips


def find_peers(response: dict) -> list[tuple[str, int]]:
    """
    The tracker may return peers in:
        a) a list of dictionaries (dictionary model)
        b) a string of bytes with multiple-of-six length (binary model)
    Option "a" is not available when the request to the tracker passes
    compact=1 as an argument, which is what this client uses by default.
    """
    peers = response[b"peers"]
    if type(peers) == dict:
        return handle_dictionary_model(peers)
    return handle_binary_model(peers)


def build_handshake(info_hash: bytes, peer_id: str) -> bytes:
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()
    return pstrlen + pstr + reserved + info_hash + peer_id


async def send_request(writer, index, begin, length):
    message = struct.pack("!IBIII", 13, Message.request, index, begin, length)
    writer.write(message)
    await writer.drain()


async def close_writer(writer: asyncio.StreamWriter):
    if not writer:
        return
    writer.close()
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout=2)
    except (asyncio.TimeoutError, ConnectionResetError, OSError):
        pass


async def handle_peer(block_info, states, endpoint, handshake, info_hash):
    ip, port = endpoint
    writer = None
    async with asyncio.Semaphore(30):
        # noinspection PyBroadException
        try:
            connection = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(connection, timeout=10)

            peer = Peer(writer, reader)
            response = await peer.send_handshake(handshake)
            if response is None: raise

        except Exception:
            pass
        finally:
            await close_writer(writer)


async def handle_peers(block_info, states, endpoints, handshake, info_hash):
    tasks = [
        asyncio.create_task(
            handle_peer(block_info, states, endpoint, handshake, info_hash)
        )
        for endpoint in endpoints
    ]
    await asyncio.gather(*tasks)


def contact_peer(decoded, response: dict, tracker_payload: dict):
    ips = find_peers(response)

    info = decoded[b"info"]

    # BUILDING HANDSHAKE
    info_hash = tracker_payload["info_hash"]
    peer_id = tracker_payload["peer_id"]
    handshake = build_handshake(info_hash, peer_id)

    # BUILDING STATES
    download_state = DownloadState(info[b"length"], info[b"name"].decode(),
                                   info[b"piece length"], info[b"pieces"])

    # PACKING STATES
    states = [download_state]

    # BUILDING DATA BLOCKS INFO
    block_size = 16384
    block_info = [block_size]

    asyncio.run(handle_peers(block_info, states, ips, handshake, info_hash))