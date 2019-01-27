"""
synology-decrypt:
 an open source (and executable) description of
 Synology's Cloud Sync encryption algorithm

Usage:
  syndecrypt (-p <password-file> | -k <private.pem> -l <public.pem>) -O <directory> <encrypted-file>...
  syndecrypt (-h | --help)

Options:
  -O <directory> --output-directory=<directory>
                           Output directory
  -p <password-file> --password-file=<password-file>
                           The file containing the decryption password
  -k <private.pem> --private-key-file=<private.pem>
                           The file containing the decryption private key
  -l <private.pem> --public-key-file=<public.pem>
                           The file containing the decryption public key
  -h --help                Show this screen.

For more information, see https://github.com/anojht/synology-cloud-sync-decrypt-tool
"""
import docopt
import os
import logging
import sys
from multiprocessing import Pool

import syndecrypt.files as files
#import files
import syndecrypt.util as util
#from syndecrypt import util

def main(args):

    if args[0] == "-p":
        arguments = {"--password-file": args[1], "--private-key-file": None, "--public-key-file": None, "--output-directory": args[2], "<encrypted-file>": args[3]}
    elif args[0] == "-k":
        arguments = {"--password-file": None, "--private-key-file": args[1], "--public-key-file": args[2], "--output-directory": args[3], "<encrypted-file>": args[4]}

    password_file_name = arguments['--password-file']
    if password_file_name != None:
        password = arguments['--password-file']
    else: password = None

    private_key_file_name = arguments['--private-key-file']
    if private_key_file_name != None:
            private_key = util._binary_contents_of(private_key_file_name)
    else: private_key = None

    public_key_file_name = arguments['--public-key-file']
    if public_key_file_name != None:
            public_key = util._binary_contents_of(public_key_file_name)
    else: public_key = None

    output_dir = arguments['--output-directory']
    output_dir = os.path.abspath(output_dir)

    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(format='%(levelname)s: %(message)s')

    f = arguments['<encrypted-file>']
    ff = os.path.abspath(f)
    fp = os.path.basename(ff)

    if os.path.isdir(ff):
        if not os.path.isdir(os.path.join(output_dir, fp)):
            output_dir = os.path.join(output_dir, fp)
            os.mkdir(output_dir)
        else:
            print("Folder already exists!")

        directories = list(os.walk(ff))

        for input_dir, _, _ in directories:
            structure = input_dir.replace(ff, output_dir, 1)
            if not os.path.isdir(structure):
                os.mkdir(structure)

        decrypt_args = []

        for input_dir, _, filenames in directories:
            for filename in filenames:
                decrypt_args.append((
                    os.path.join(input_dir, filename),
                    os.path.join(input_dir.replace(ff, output_dir, 1), filename),
                    password,
                    private_key,
                    public_key,
                ))

        with Pool() as p:
            p.starmap(files.decrypt_file, decrypt_args)

    else:
        files.decrypt_file(ff, os.path.join(output_dir, fp), password=password, private_key=private_key, public_key=public_key)


if __name__ == '__main__':
    main(sys.argv[1:])
