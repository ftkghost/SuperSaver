import base64
import hashlib
import hmac
import json

from .exception import InvalidSignature

ALGO_HMAC_SHA256 = 'hmac-sha256'


def encrypt_code(to_encode_data, secret, algorithm=ALGO_HMAC_SHA256):
    """
    Encrypt data with secret
    :param to_encode_data: data to encrypt. (builtin types, list, dict)
    :param secret: app secret (str).
    :param algorithm: encryption algorithm.
    :return: str of signed data.
    """
    data = {
        'data': to_encode_data,
        'algo': algorithm
    }
    data_bytes = json.dumps(data).encode('utf-8')
    encoded_data_bytes = base64.urlsafe_b64encode(data_bytes)

    # HMAC can only handle ascii (byte) strings
    # http://bugs.python.org/issue5285
    secret_bytes = secret.encode('ascii')
    if algorithm == ALGO_HMAC_SHA256:
        sig_bytes = hmac.new(secret_bytes, msg=encoded_data_bytes, digestmod=hashlib.sha256).digest()
        encoded_sig_bytes = base64.urlsafe_b64encode(sig_bytes)
    else:
        raise ValueError('Unsupported algorithm ' + algorithm)
    encoded_data_str = encoded_data_bytes.decode('ascii')
    encoded_sig_str = encoded_sig_bytes.decode('ascii')
    signed_code = '{0}${1}'.format(encoded_data_str, encoded_sig_str)
    return signed_code


def decrypt_code(signed_code, secret):
    """
    Decrypt signed code with secret.
    :param signed_code: signed secret code (str).
    :param secret: app secret (str)
    :return: decrypted data.
    """
    items = signed_code.split('$', 1)
    if len(items) != 2:
        raise InvalidSignature('Invalid secret code.')
    encoded_data_str = items[0] + ("=" * ((4 - len(items[0]) % 4) % 4))
    encoded_sig_str = items[1] + ("=" * ((4 - len(items[1]) % 4) % 4))
    encoded_data_bytes, encoded_sig_bytes = encoded_data_str.encode('ascii'), encoded_sig_str.encode('ascii')
    try:
        data_bytes = base64.urlsafe_b64decode(encoded_data_bytes)
        sig_bytes = base64.urlsafe_b64decode(encoded_sig_bytes)
    except Exception as e:
        raise InvalidSignature(e.message)
    # HMAC can only handle ascii (byte) strings
    # http://bugs.python.org/issue5285
    secret_bytes = secret.encode('ascii')
    expected_sig_bytes = hmac.new(secret_bytes, msg=encoded_data_bytes, digestmod=hashlib.sha256).digest()
    if sig_bytes != expected_sig_bytes:
        raise InvalidSignature('Invalid signature in secret code.')

    data_dict = json.loads(data_bytes.decode('utf-8'))
    if 'data' not in data_dict or 'algo' not in data_dict:
        raise InvalidSignature('Invalid data in secret code.')
    algo = data_dict['algo']
    if algo != ALGO_HMAC_SHA256:
        raise InvalidSignature('Invalid algorithm in secret code.')
    return data_dict['data']
