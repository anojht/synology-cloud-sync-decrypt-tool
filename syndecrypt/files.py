from __future__ import print_function
import os
import sys
import logging

import syndecrypt.core as core
#import core

LOGGER=logging.getLogger(__name__)

def decrypt_file(input_file_name, output_file_name, password=None, private_key=None, public_key=None):
        if not os.path.exists(input_file_name):
                LOGGER.warn('skipping decryption of "%s": encrypted input file does not exist',
                        input_file_name
                )
                return
        if os.path.exists(output_file_name):
                LOGGER.warn('skipping decryption of "%s": chosen output file "%s" already exists',
                        input_file_name, output_file_name
                )
                return
        LOGGER.info('decrypting "%s" to "%s"', input_file_name, output_file_name)
        try:
                with open(input_file_name, 'rb') as instream:
                        if not os.path.isdir(os.path.dirname(output_file_name)):
                                os.makedirs(os.path.dirname(output_file_name))
                        with open(output_file_name, 'wb') as outstream:
                                core.decrypt_stream(instream, outstream, password=password, private_key=private_key, public_key=public_key)
        except:
                LOGGER.error('decryption failed, exception occurred: %s: %s', sys.exc_info()[0], sys.exc_info()[1])
                if os.path.exists(output_file_name):
                        os.remove(output_file_name)
                raise
