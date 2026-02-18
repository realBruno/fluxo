import struct


def dictionary(peers: dict) -> list[tuple[str, int]]:
    """Processes dictionaries with IP addresses of peers.

    :param peers: A dictionary with peer's data.
    :returns: A list of tuples with IP address (str) and port (int) of peer(s).
    """
    endpoints = []
    for peer in peers:
        ip = peer[b"ip"].decode()
        endpoints.append((ip, peer[b"port"]))
    return endpoints


def binary(peers: bytes) -> list[tuple[str, int]]:
    """Processes byte-string with IP addresses of peers.

    :param peers: A multiple-of-six length byte-string with peer's data.
    :returns: A list of tuples with IP address (str) and port (int) of peer(s).
    """
    endpoints = []
    for chunk in (peers[i: i + 6] for i in range(0, len(peers), 6)):
        ip = '.'.join(map(str, chunk[:4]))
        if ip != "127.0.0.1":
            port = struct.unpack("!H", chunk[4:])[0]
            endpoint = (ip, port)
            endpoints.append(endpoint)
    return endpoints


def sock_addr(response: dict) -> list[tuple[str, int]]:
    """
    The tracker may return peers in:
        1. a list of dictionaries (dictionary model)
        2. a string of bytes (binary model)
    First option is not available when the request to the tracker passes
    compact=1 as an argument, which is what this client uses by default.

    :param response: A dictionary containing the tracker's response.
    :returns: A list of tuples with IP address (str) and port (int) of peer(s).
    """
    peers = response[b"peers"]
    if type(peers) == list:
        return dictionary(peers)
    return binary(peers)