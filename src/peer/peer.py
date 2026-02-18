from dataclasses import dataclass

import asyncio


@dataclass
class Peer:
    writer: asyncio.StreamWriter
    reader: asyncio.StreamReader

    peer_choking: bool = True       # peer is choking this client
    peer_interested: bool = False   # peer is interested in this client

    am_choking: bool = True         # this client is choking the peer
    am_interested: bool = False     # this client is interested in the peer