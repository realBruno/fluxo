import sys

from client import request

def show_progress():
    ...

def get_path():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    elif len(sys.argv) == 1:
        path = input()
    else:
        raise TypeError(f"Takes exactly 1 argument. {len(sys.argv) - 1} given.")

    make_request(path)

def make_request(path: str):
    decoded, hashed = request.get_file_info(path)
    request.torrent(decoded, hashed)

# get_path()