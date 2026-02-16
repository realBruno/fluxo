"""
    Torrent client program.
    Author: Bruno Fernandes (github.com/realBruno)
    Date: 24/jan/2026
"""
import sys

from client import modes, peer


def make_request(path: str):
    print("Parsing metadata...")
    decoded, info_hash, is_single = modes.get_file_info(path)
    announce = decoded[b"announce"]
    if is_single:
        print("Building payload...")
        payload = modes.single_torrent(decoded, info_hash)
        print("Submitting request...")
        response = modes.submit(announce, payload)
        print("Request was successful!")
        print("Starting contact with peers...")
        info_hash = payload["info_hash"]
        peer_id = payload["peer_id"]
        peer.contact_peer(response, info_hash, peer_id)
    else:
        raise TypeError("Multi-file mode is under development")


def get_path():
    if len(sys.argv) == 2:
        return sys.argv[1]
    elif len(sys.argv) == 1:
        return input("Path to file: ")
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")


file_loc = get_path()
make_request(file_loc)
