from dataclasses import dataclass
import asyncio
import struct

from typing import Any
from peer.messages import Message


@dataclass
class PeerProtocol:
    writer: asyncio.StreamWriter
    reader: asyncio.StreamReader

    async def send_handshake(self, handshake: bytes) -> bytes | None:
        """Sends first ever message to peer.

        :param handshake: Handshake message
        :returns: The peer's handshake bytes if valid, otherwise None
        """
        self.writer.write(handshake)
        await self.writer.drain()
        return await self.read_handshake(handshake)

    async def read_handshake(self, handshake: bytes) -> bytes | None:
        """ Reads and validates peer's handshake.

        Each handshake should be 68 bytes long. The info_hash
        of the response, which is 20 bytes long and is located at
        positions 28 to 48, should equal the client's info_hash.

        :param handshake: Handshake message.
        :returns: The peer's handshake bytes if valid, otherwise None.
        """
        response = await asyncio.wait_for(
            self.reader.readexactly(68), timeout=10
        )
        if response[28:48] == handshake[28:48]:
            return response
        return None

    async def send_interested(self, peer):
        """ Informs peer that the client is interested in pieces they own.

            Peer's responds with one of the values in the "Message" dataclass.
        """
        message = struct.pack("!IB", 1, Message.interested)
        peer.am_choking = False
        self.writer.write(message)
        await self.writer.drain()

    async def send_keep_alive(self):
        ...

    @staticmethod
    async def handle_unchoke(peer):
        peer.is_choking = False

    async def handle_piece(self, length: int = 1):
        ...

    async def handle_bitfield(self, length: int):
        ...

    async def handle_request(self, index, begin, length):
        message = struct.pack("!IBIII", 13,
                              Message.request, index, begin, length)
        self.writer.write(message)
        await self.writer.drain()

    async def handle_response(self, peer, length, message_id):
        match message_id:
            # case 0: await self.handle_choke()
            case Message.unchoke:
                await self.handle_unchoke(peer)
            # case 2: await self.handle_interested()
            # case 3: await self.handle_not_interested()
            # case 4: await self.handle_have()
            case Message.bitfield:
                await self.handle_bitfield(length)
            # case 6: await self.handle_request()
            case Message.piece:
                await self.handle_piece()
            # case 8: await self.handle_cancel()
            # case 9: await self.handle_port()

    async def read_response(self) -> tuple[int, Any, Any]:
        """Reads response from peer.

        The response from a peer may vary in length:
        If length is 0, peer is sending a "keep-alive" message.
        If 1, it sent requests of (un)choke or (not) interested.
        Otherwise, peer has sent data on the files requested.

        :return: A tuple with length, and message_id and payload or None
        """
        length = await self.reader.readexactly(4)
        length = struct.unpack("!I", length)[0]
        if length == 0:
            return length, None, None

        message_id = await self.reader.readexactly(1)
        message_id = struct.unpack("!B", message_id)[0]
        if length == 1:
            return length, message_id, None

        payload = await self.reader.readexactly(length - 1)
        return length, message_id, payload