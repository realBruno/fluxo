import requests
import hashlib
import random
import binascii

from client import bencode


def submit(announce: bytes, queries: dict) -> dict:
    response = None

    if b"udp://" in announce:
        raise ConnectionError("Client doesn't support UDP protocol")

    for i in range(9):  # make 9 attempts to connect before giving up
        queries["port"] += i
        response = requests.get(announce, params=queries)
        decoded_response = bencode.decode(response.content)

        if b"failure reason" in decoded_response:
            raise ConnectionError(decoded_response[b"failure reason"])
        if b"warning message" in decoded_response:
            print(f'WARNING: {decoded_response[b"warning message"]}')
        if response.status_code == 200:
            return decoded_response
    raise ConnectionError(f"{[response.status_code]}: {response.reason}")


# SINGLE FILE MODE
def single_torrent(decoded: dict, info_hash: str):
    queries = payload(info_hash)
    queries["left"] = decoded[b"info"][b"length"]
    return queries


# AUXILIARY FUNCTIONS
def get_file_info(path: str) -> tuple[dict, str, int]:
    decoded = bencode.decode(path)
    info_hash = hashlib.sha1(bencode.encode(decoded[b"info"])).digest().hex()
    single_file = b"files" not in decoded[b"info"]

    return decoded, info_hash, single_file


def payload(info_hash: str) -> dict:
    client_id = "PY"
    client_version = "0001"
    query = {
        "info_hash": binascii.unhexlify(info_hash),
        "peer_id": '-' + client_id + client_version + '-' +
                   ''.join(str(
                       random.randint(0, 9)
                   ) for _ in range(12)),
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "left": 0,
        "compact": 1,
        "no_peer_id": 0,  # ignored if compact is available
        "event": "started",
    }

    return query
