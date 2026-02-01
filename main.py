"""
    Torrent client program.
    Author: Bruno Fernandes (github.com/realBruno)
    Date: 24/jan/2026
"""

import sys
from src.client.bencode import Bencode

if len(sys.argv) == 2:
    path = sys.argv[1].replace("\"", '')
    parsed = Bencode.decode(path)
elif len(sys.argv) == 1:
    parsed = Bencode.decode((path := input()).replace("\"",''))
else:
    raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")

print(parsed)