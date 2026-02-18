import asyncio

from  peer.peer import Peer
from peer.protocol import PeerProtocol
from tracker.endpoints import sock_addr


def build_handshake(info_hash: bytes, peer_id: str) -> bytes:
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr).to_bytes(1, byteorder="big")
    reserved = bytes(8)
    info_hash = info_hash
    peer_id = peer_id.encode()
    return pstrlen + pstr + reserved + info_hash + peer_id


async def close_writer(writer: asyncio.StreamWriter):
    if not writer:
        return
    writer.close()
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout=2)
    except (asyncio.TimeoutError, ConnectionResetError, OSError):
        pass


async def handle_peer(endpoint, handshake):
    ip, port = endpoint
    writer = None
    async with asyncio.Semaphore(30):
        # noinspection PyBroadException
        try:
            connection = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(connection, timeout=10)

            peer = Peer(writer, reader)
            peer_protocol = PeerProtocol(writer, reader)

            peer_handshake = await peer_protocol.send_handshake(handshake)
            if peer_handshake is None: raise # drops connection with peer

            await peer_protocol.send_interested(peer)

            while True:
                length, message_id, payload = await peer_protocol.read_response()
                print(length, message_id, payload)
                if message_id is not None:
                    await peer_protocol.handle_response(peer, length, message_id)
        except Exception:
            pass
        finally:
            await close_writer(writer)


async def handle_peers(endpoints, handshake):
    tasks = [
        asyncio.create_task(
            handle_peer(endpoint, handshake)
        )
        for endpoint in endpoints
    ]
    await asyncio.gather(*tasks)


def contact_peer(decoded, response: dict, tracker_payload: dict):
    endpoints = sock_addr(response)

    if len(endpoints) > 30:
        endpoints = endpoints[:30]

    # BUILDING HANDSHAKE
    info_hash = tracker_payload["info_hash"]
    peer_id = tracker_payload["peer_id"]
    handshake = build_handshake(info_hash, peer_id)

    asyncio.run(handle_peers(endpoints, handshake))