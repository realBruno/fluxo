from dataclasses import dataclass


@dataclass
class Download:
    """Keeps track of information on the download."""
    file_size: int
    filename: str
    piece_length: int
    total_pieces: int
    interval: int
    complete: int
    incomplete: int