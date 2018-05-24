#import syndecrypt.util as util
import util
from util import switch

from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import hashlib

import logging
import struct
from collections import OrderedDict
import base64

LOGGER=logging.getLogger(__name__)

# Thanks to http://security.stackexchange.com/a/117654/3617,
# this is the algorithm by which 'openssl enc' generates
# a key and an iv from a password.
#
# Sources for this algorithm:
# - https://github.com/openssl/openssl/blob/OpenSSL_1_0_1m/apps/enc.c#L540
#   and https://github.com/openssl/openssl/blob/OpenSSL_1_0_1m/apps/enc.c#L347
# - https://github.com/openssl/openssl/blob/OpenSSL_1_0_1m/crypto/evp/evp_key.c#L119
#   and https://www.openssl.org/docs/manmaster/crypto/EVP_BytesToKey.html
#
# Synology Cloud Sync encryption/decryption uses the same
# algorithm to generate key+iv from the password.

# pwd and salt must be bytes objects
def _openssl_kdf(algo, pwd, salt, key_size, iv_size, iteration):
    temp = b''

    fd = temp
    while len(fd) < key_size + iv_size:
        temp = _hasher(algo, temp + pwd + salt, iteration)
        fd += temp

    key = fd[0:key_size]
    iv = fd[key_size:key_size+iv_size]

    return key, iv

def _hasher(algo, data, iteration):
    digest = data
    for i in xrange(iteration):
        h = hashlib.new(algo)
        h.update(digest)
        digest = h.digest()
    return digest

# From pyaes, since pycrypto does not implement padding

def strip_PKCS7_padding(data):
    if len(data) % 16 != 0:
        raise ValueError("invalid length")
    pad = bytearray(data)[-1]
    if pad > 16:
        raise ValueError("invalid padding byte at end of " + repr(data[-32:]))
    for i in range(-pad, 0):
        if bytearray(data)[i] != pad:
            raise ValueError("invalid padding byte at " + str(i) + " in " + repr(data[-32:]))
    return data[:-pad]


def decrypted_with_password(ciphertext, password, salt):
        decryptor = _decryptor_with_keyiv(_csenc_pbkdf(password, salt, iteration=1000))
        plaintext = decryptor_update(decryptor, ciphertext)
        return plaintext

def decrypted_with_private_key(ciphertext, private_key):
        return PKCS1_OAEP.new(RSA.importKey(private_key)).decrypt(ciphertext)

def decryptor_with_password(password, salt=b''):
        return _decryptor_with_keyiv(_csenc_pbkdf(password.decode('hex'), salt))

def _csenc_pbkdf(password, salt, iteration=1):
        AES_KEY_SIZE_BITS = 256
        AES_IV_LENGTH_BYTES = AES.block_size
        assert AES_IV_LENGTH_BYTES == 16
        (key, iv) = _openssl_kdf('md5', password, salt, AES_KEY_SIZE_BITS//8, AES_IV_LENGTH_BYTES, iteration)
        return (key, iv)

def _decryptor_with_keyiv(key_iv_pair):
        (key, iv) = key_iv_pair
        return AES.new(key, AES.MODE_CBC, iv)

def decryptor_update(decryptor, ciphertext):
        return strip_PKCS7_padding(decryptor.decrypt(ciphertext))

def salted_hash_of(salt, data):
        m = hashlib.md5()
        m.update(salt.encode('ascii'))
        m.update(data)
        return salt + m.hexdigest()

def is_salted_hash_correct(salted_hash, data):
        return salted_hash_of(salted_hash[:10], data) == salted_hash

def _read_objects_from(f):
        result = []
        while True:
                obj = _read_object_from(f)
                if obj == None: break
                result += [obj]
        return result

def _read_object_from(f):
        s = f.read(1)
        if len(s) == 0: return None
        header_byte = bytearray(s)[0]
        if header_byte == 0x42:
                return _continue_read_ordered_dict_from(f)
        elif header_byte == 0x40:
                return None
        elif header_byte == 0x11:
                return _continue_read_bytes_from(f)
        elif header_byte == 0x10:
                return _continue_read_string_from(f)
        elif header_byte == 0x01:
                return _continue_read_int_from(f)
        else:
                raise Exception('unknown type byte ' + ("0x%02X" % header_byte))

# def _read_dict_from(f, d):
#         while True:
#             d,  = _read_object_from2(f, d)


def _continue_read_ordered_dict_from(f):
        result = OrderedDict()
        while True:
                key = _read_object_from(f)
                if key == None: break
                value = _read_object_from(f)
                result[key] = value
        return result

def _continue_read_bytes_from(f):
        s = f.read(2)
        length = struct.unpack('>H', s)[0]
        return f.read(length)

def _continue_read_string_from(f):
        return _continue_read_bytes_from(f).decode('utf-8')

def _continue_read_int_from(f):
        s = f.read(1)
        length = struct.unpack('>B', s)[0]
        if length > 1:
                LOGGER.warning('multi-byte number encountered; guessing it is big-endian')
        s = f.read(length)
        if length > 0 and bytes_to_bigendian_int(s[:1]) >= 128:
                LOGGER.warning('ambiguous number encountered; guessing it is positive')
        return bytes_to_bigendian_int(s) # big-endian integer, 'length' bytes

def bytes_to_bigendian_int(b):
        import binascii
        return int(binascii.hexlify(b), 16) if b != b'' else 0

def read_header(f):
        MAGIC = b'__CLOUDSYNC_ENC__'

        s = f.read(len(MAGIC))
        if s != MAGIC:
                LOGGER.error('magic should not be ' + str(s) + ' but ' + str(MAGIC))
        s = f.read(32)
        magic_hash = hashlib.md5(MAGIC).hexdigest().encode('ascii')
        if s != magic_hash:
                LOGGER.error('magic hash should not be ' + str(s) + ' but ' + str(magic_hash))

        header = _read_object_from(f)
        if header['type'] != 'metadata':
                LOGGER.error('first object must have "metadata" type but found ' + header['type'])
        return header

def read_chunks(f):
        while True:
                chunk = _read_object_from(f)
                if not chunk: return
                yield chunk

def decrypt_stream(instream, outstream, password=None, private_key=None, public_key=None):

        session_key = None
        decryptor = None
        decrypt_stream.md5_digestor = None # special kind of local variable...
        expected_md5_digest = None

        def outstream_writer_and_md5_digestor(decompressed_chunk):
                outstream.write(decompressed_chunk)
                if decrypt_stream.md5_digestor != None:
                        decrypt_stream.md5_digestor.update(decompressed_chunk)

        # create session key and decryptor
        header = read_header(instream)
        # TODO: assert version and hash algo
        decrypt_stream.md5_digestor = hashlib.md5()
        if   password != None:
                # password
                actual_password_hash = salted_hash_of(header['key1_hash'][:10], password)
                if header['key1_hash'] != actual_password_hash:
                        LOGGER.warning('found key1_hash %s but expected %s', actual_password_hash, header['key1_hash'])
                session_key = decrypted_with_password(base64.b64decode(header['enc_key1'].encode('ascii')), password, header['salt'].encode('ascii'))
                decryptor = decryptor_with_password(session_key)
        elif private_key != None and public_key != None:
                # RSA
                actual_public_key_hash = salted_hash_of(header['key2_hash'][:10], public_key)
                if header['key2_hash'] != actual_public_key_hash:
                        LOGGER.warning('found key2_hash %s but expected %s', actual_public_key_hash, header['key2_hash'])
                session_key = decrypted_with_private_key(base64.b64decode(header['enc_key2'].encode('ascii')), private_key)
                decryptor = decryptor_with_password(session_key)
        else:
                raise Exception("Key material is not found")
        actual_session_key_hash = salted_hash_of(header['session_key_hash'][:10], session_key)
        if header['session_key_hash'] != actual_session_key_hash:
                LOGGER.warning('found session_key_hash %s but expected %s', actual_session_key_hash, header['session_key_hash'])

        # decrypt chunks
        data = b''
        with util.Lz4Decompressor(decompressed_chunk_handler=outstream_writer_and_md5_digestor) as decompressor:
                for chunk in read_chunks(instream):
                        if   chunk['type'] == 'metadata':
                                # decrypt file
                                decrypted_data = decryptor_update(decryptor, data)
                                decompressor.write(decrypted_data)
                                #
                                expected_md5_digest = chunk['file_md5']
                                break
                        elif chunk['type'] == 'data':
                                data += chunk['data']
                        else:
                                raise Exception("Bad chunk found: " + str(chunk))
        # verify md5
        if decrypt_stream.md5_digestor != None and expected_md5_digest != None:
                actual_md5_digest = decrypt_stream.md5_digestor.hexdigest()
                if actual_md5_digest != expected_md5_digest:
                        raise Exception('expected md5 digest %s but found %s', expected_md5_digest, actual_md5_digest)
