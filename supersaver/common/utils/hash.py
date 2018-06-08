import hashlib


def calculate_hash(obj):
    """
    Calculate obj md5 hash
    :param obj: a str/bytes/file object.
    :return: hash string.
    """
    if isinstance(obj, str):
        obj_bytes = str.encode('utf-8')
    elif isinstance(obj, bytes):
        obj_bytes = bytes
    elif hasattr(obj, 'seek') and callable(obj.seek) and hasattr(obj, 'read') and callable(obj.read):
        obj.seek(0)
        obj_bytes = obj.read()
    else:
        raise ValueError('Unsupported target object for hashing.')
    hash_calc = hashlib.md5()
    hash_calc.update(obj_bytes)
    return hash_calc.hexdigest()
