from dataclasses import dataclass


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