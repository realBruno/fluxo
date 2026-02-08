"""
    Torrent client program.
    Author: Bruno Fernandes (github.com/realBruno)
    Date: 24/jan/2026
"""
import sys

from client import bencode, modes, peer, support

def make_request(path: str):
    print("Parsing metadata...", end = '')
    decoded, info_hash, is_single = support.get_file_info(path)
    announce = decoded[b"announce"]
    if is_single:
        print("\rBuilding payload...", end = '')
        payload = modes.single_torrent(decoded, info_hash)
        print("\rSubmitting request...", end = '')
        response = modes.submit(announce, payload)
        print("\rRequest successful!", end = '')
        response = bencode.parse(response, 0)[0]
        print("\rStarting handshake with peers...", end = '')
        peer.handshake(response)
    else:
        raise TypeError("Multi-file mode is under development")

def get_path():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    elif len(sys.argv) == 1:
        path = input("Path to file: ")
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")
    make_request(path)

get_path()