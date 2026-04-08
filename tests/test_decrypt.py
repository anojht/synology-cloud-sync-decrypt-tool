from __future__ import print_function

import syndecrypt.core as core
import syndecrypt.util as util
import collections

from assertpy import assert_that
import base64
import io
import logging

LOGGER=logging.getLogger(__name__)

PASSWORD=util._binary_contents_of('tests/testfiles-secrets/password.txt')
PRIVATE_KEY=util._binary_contents_of('tests/testfiles-secrets/private.pem')


def test_decode_int():
        assert core._continue_read_int_from(io.BytesIO(b'\x00')) == 0
        assert core._continue_read_int_from(io.BytesIO(b'\x01\x02')) == 2
        assert core._continue_read_int_from(io.BytesIO(b'\x01\x82')) == 128 + 2
        assert core._continue_read_int_from(io.BytesIO(b'\x02\x80\x02')) == 32768 + 2


def test_decrypt_enc_key1():
        """
        Test that we can do the equivalent of

          $ echo 'f662PyjwrkzR61qSRHyBEVkXVd7STUpV6o7IrJs+m8gN1haqmBtMzLvq2/Gj134r' | openssl enc -aes256 -d -a -pass pass:'buJx9/y9fV' -nosalt
          BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6
        """

        enc_key1 = b'f662PyjwrkzR61qSRHyBEVkXVd7STUpV6o7IrJs+m8gN1haqmBtMzLvq2/Gj134r'
        enc_key1_binary = base64.b64decode(enc_key1)
        assert core.decrypted_with_password(enc_key1_binary, PASSWORD) == b'BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6'

def test_decrypt_enc_key2():
        """
        Test that we can do the equivalent of

          $ echo 'ovVar7Zpi0HVPZ3CGmXRBhp4l1Q1BNNo0/uYfdwSg1GDD/MXNSMXcuAf65pYObUQsu4aCQc82LldLINkUSFyoPYUDe5YKh4Fv3993YQ7CPYk5RrWem2CGntdjmS1J5KV9YHa7bF2l6wMT2FiFvfd+/3Pikadb/fqOC/hN5hx2kA2c5n3FltCGehhfW97Bb3aLEZaOJ8rpoPuHDIa6yxhstCHrajnb0870KprqSfFZUdin1G1hqpwJ+1gm7CmFkjKA6QqMD5dx7bru69g98VwrqYqGmYR3lmJuMI0wJn7WwbciWCOQV5fnfMMxiAiZ0DK1fseqWxMIYUk3lVOcAA3KA==' \
              | base64 -d | openssl rsautl -decrypt -inkey tests/testfiles-secrets/private.pem -oaep
          BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6
        """
        enc_key2 = b'ovVar7Zpi0HVPZ3CGmXRBhp4l1Q1BNNo0/uYfdwSg1GDD/MXNSMXcuAf65pYObUQsu4aCQc82LldLINkUSFyoPYUDe5YKh4Fv3993YQ7CPYk5RrWem2CGntdjmS1J5KV9YHa7bF2l6wMT2FiFvfd+/3Pikadb/fqOC/hN5hx2kA2c5n3FltCGehhfW97Bb3aLEZaOJ8rpoPuHDIa6yxhstCHrajnb0870KprqSfFZUdin1G1hqpwJ+1gm7CmFkjKA6QqMD5dx7bru69g98VwrqYqGmYR3lmJuMI0wJn7WwbciWCOQV5fnfMMxiAiZ0DK1fseqWxMIYUk3lVOcAA3KA=='
        enc_key2_binary = base64.b64decode(enc_key2)

        assert core.decrypted_with_private_key(enc_key2_binary, PRIVATE_KEY) == b'BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6'


def test_salted_hash():
        session_key = b'BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6'
        session_key_hash = 'jM41by6vAd517830d42bfb52eae9b58cd41eac95b0'
        assert core.salted_hash_of(session_key_hash[:10], session_key) == session_key_hash
        assert core.is_salted_hash_correct(session_key_hash, session_key)

        password_hash = '4ZF3pd4Y17c7cf0f016aada3f8398d22c8708d8649'
        assert core.salted_hash_of(password_hash[:10], PASSWORD) == password_hash
        assert core.is_salted_hash_correct(password_hash, PASSWORD)


def lz4_uncompress(compressed_data):
        result = io.BytesIO()
        with util.Lz4Decompressor(decompressed_chunk_handler=result.write) as decompressor:
                decompressor.write(compressed_data)
        return result.getvalue()

def test_decode_single_line_file():
        with open('tests/testfiles-csenc/single-line.txt', 'rb') as f:
                s = core.decode_csenc_stream(f)
                assert next(s) == ('compress', 1)
                assert next(s) == ('digest', 'md5')
                assert next(s) == ('enc_key1', 'f662PyjwrkzR61qSRHyBEVkXVd7STUpV6o7IrJs+m8gN1haqmBtMzLvq2/Gj134r')
                assert next(s) == ('enc_key2', 'ovVar7Zpi0HVPZ3CGmXRBhp4l1Q1BNNo0/uYfdwSg1GDD/MXNSMXcuAf65pYObUQsu4aCQc82LldLINkUSFyoPYUDe5YKh4Fv3993YQ7CPYk5RrWem2CGntdjmS1J5KV9YHa7bF2l6wMT2FiFvfd+/3Pikadb/fqOC/hN5hx2kA2c5n3FltCGehhfW97Bb3aLEZaOJ8rpoPuHDIa6yxhstCHrajnb0870KprqSfFZUdin1G1hqpwJ+1gm7CmFkjKA6QqMD5dx7bru69g98VwrqYqGmYR3lmJuMI0wJn7WwbciWCOQV5fnfMMxiAiZ0DK1fseqWxMIYUk3lVOcAA3KA==')
                assert next(s) == ('encrypt', 1)
                assert next(s) == ('file_name', 'single-line.txt')
                assert next(s) == ('key1_hash', '4ZF3pd4Y17c7cf0f016aada3f8398d22c8708d8649')
                assert next(s) == ('key2_hash', 'Hs2fAqiRaTb73da9c06e2b824dc3a9935ae71bdd14')
                assert next(s) == ('session_key_hash', 'jM41by6vAd517830d42bfb52eae9b58cd41eac95b0')
                assert next(s) == ('version', collections.OrderedDict([('major', 1), ('minor', 0)]))
                (none, data) = next(s)
                assert none == None and isinstance(data, bytes) # a chunk of encrypted compressed data
                assert next(s) == ('file_md5', 'e45f14e62971070603ff27c2bb05f5a4')

                session_key = b'BxY2A-ouRpI8YRvmiWii5KkCF3LVN1O6'
                decrypted_compressed_data = core.decrypted_with_password(data, session_key)
                decrypted_uncompressed_data = lz4_uncompress(decrypted_compressed_data)
                assert decrypted_uncompressed_data == b'Just a single line, no newline character at the end...'


def test_decrypt_single_line_stream_with_password():
        outstream = io.BytesIO()
        with open('tests/testfiles-csenc/single-line.txt', 'rb') as f:
                core.decrypt_stream(f, outstream, password=PASSWORD)
        assert outstream.getvalue() == b'Just a single line, no newline character at the end...'

def test_decrypt_single_line_stream_with_private_key():
        outstream = io.BytesIO()
        with open('tests/testfiles-csenc/single-line.txt', 'rb') as f:
                core.decrypt_stream(f, outstream, private_key=PRIVATE_KEY)
        assert outstream.getvalue() == b'Just a single line, no newline character at the end...'

def test_decrypt_single_line_stream_fails_without_key():
        outstream = io.BytesIO()
        try:
                with open('tests/testfiles-csenc/single-line.txt', 'rb') as f:
                        core.decrypt_stream(f, outstream)
                assert False, 'expected exception'
        except Exception as e:
                assert_that(e.args[0]).matches('not enough information to decrypt')
