def value(v: list | dict | str | int):
    content = ''
    match v:
        case list():
            content += 'l'
            for item in v:
                content += value(item)
            content += 'e'
        case dict():
            content += 'd'
            for key, val in v.items():
                content += value(key)
                content += value(val)
            content += 'e'
        case int():
            content += 'i' + str(v) + 'e'
        case str():
            content += str(len(v)) + ':' + str(v)

    return content

def encode(parsed: dict):
    if type(parsed) != dict:
        raise ValueError("Data is not a dictionary")

    bencoded = 'd'
    for k, v in parsed.items():
        bencoded += str(len(k)) + ':' + str(k)
        bencoded += value(v)
    return bencoded