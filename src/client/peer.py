import struct
import socket
import asyncio
from colorama import Fore
from enum import Enum


HANDSHAKE_SIZE = 68

class MESSAGE(Enum):
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6


def get_ips(response: dict):
    ips = []
    peers = response[b"peers"]

    if type(peers) == dict: return ips

    for i in range(0, len(peers) - 6, 6):
        chunk = peers[i: i + 6]
        ip = '.'.join(str(b) for b in chunk[0:4])
        if ip != "127.0.0.1":
            port = struct.unpack("!H", chunk[4: 6])[0]
            ips.append((ip, port))
    return ips


def build_handshake(info_hash, peer_id):
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()
    return pstrlen + pstr + reserved + info_hash + peer_id


def validate_handshake(response, info_hash):
    if len(response) < HANDSHAKE_SIZE or response[28:48] != info_hash:
        print(Fore.YELLOW + "Peer responded with malformed answer." + Fore.RESET)
        return 0
    print(Fore.GREEN + "Peer responded successfully." + Fore.RESET)
    return 1


async def send_handshake(handshake, writer, reader, info_hash):
    writer.write(handshake)
    await writer.drain()

    response = await asyncio.wait_for(
        reader.read(HANDSHAKE_SIZE), timeout=10
    )

    valid = validate_handshake(response, info_hash)

    return response if valid else None


async def send_interested(writer):
    message = struct.pack("!IB", 1, MESSAGE.INTERESTED.value)
    writer.write(message)
    await writer.drain()


async def receive_message(reader):
    size = await reader.readexactly(4)
    size = struct.unpack("!I", size)[0]

    if size == 0:
        return 0, None, None

    message_type = await reader.readexactly(1)
    message_type = struct.unpack("!B", message_type)[0]

    payload = await reader.readexactly(size - 1)[0] if size - 1 > 0 else None

    return size, message_type, payload

async def connect_to_peer(endpoint, handshake, info_hash, semaphore):
    ip, port = endpoint
    writer = None
    async with semaphore:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=10
            )

            response = await send_handshake(
                handshake, writer, reader, info_hash
            )

            if response is None: raise Exception

            await send_interested(writer)

            while True:
                await receive_message(reader)

        except asyncio.TimeoutError:
            print(Fore.RED + f"Peer did not respond" + Fore.RESET)
        except ConnectionError as c:
            print(Fore.RED + f"Connection error: {c}" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}" + Fore.RESET)
        finally:
            if writer:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=2)
                except (asyncio.TimeoutError, ConnectionResetError, OSError):
                    pass


async def connect_to_peers(endpoints, handshake, info_hash):
    MAX_CONNECTIONS = 30
    semaphore = asyncio.Semaphore(MAX_CONNECTIONS)
    tasks = [
        asyncio.create_task(
            connect_to_peer(endpoint,handshake, info_hash, semaphore)
        )
        for endpoint in endpoints
    ]
    await asyncio.gather(*tasks)


def contact_peer(response: dict, info_hash, peer_id):
    ips = get_ips(response)
    handshake = build_handshake(info_hash, peer_id)
    asyncio.run(connect_to_peers(ips, handshake, info_hash))