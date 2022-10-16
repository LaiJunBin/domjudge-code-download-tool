import base64, random, string, json


def base64_encoding(message):
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message


def file2blob(file):
    base64_bytes = base64.b64encode(file.read())
    base64_message = base64_bytes.decode('ascii')
    return base64_message


def dict2blob(dict):
    json_str = json.dumps(dict).encode()
    base64_bytes = base64.b64encode(json_str)
    base64_message = base64_bytes.decode('ascii')
    return base64_message


def base64_decode(b64data):
    try:
        return base64.b64decode(b64data).decode('utf-8')
    except:
        pass

    try:
        return base64.b64decode(b64data).decode('gb2312')
    except:
        pass

    return base64.b64decode(b64data)


def random_ascii_letters(length=6):
    return ''.join([random.choice(string.ascii_letters) for _ in range(length)])
