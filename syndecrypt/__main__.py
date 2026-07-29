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
import logging
import os
import sys
from multiprocessing.pool import ThreadPool

import docopt

import syndecrypt.files as files
#import files
import syndecrypt.util as util
#from syndecrypt import util
from syndecrypt.core import EcryptfsFileError

# Synology's *encrypted shared folder* feature uses eCryptfs, which is a
# completely different format from Cloud Sync. Files in those folders have
# this filename prefix. We check up-front and raise a clear error rather
# than letting the Cloud Sync parser explode on a stack trace.
ECRYPTFS_PREFIX = "ECRYPTFS_FNEK_ENCRYPTED."

def _check_not_ecryptfs(name):
    if os.path.basename(name).startswith(ECRYPTFS_PREFIX):
        raise EcryptfsFileError(
            "'%s' looks like a Synology eCryptfs encrypted shared folder file, "
            "not a Cloud Sync encrypted file. This tool only handles Cloud Sync "
            "output. See https://kb.synology.com/en-global/DSM/tutorial/How_to_encrypt_and_decrypt_shared_folders_on_my_Synology_NAS "
            "for decrypting eCryptfs shares." % os.path.basename(name)
        )

def _password_from_file(file_name):
    """Read the decryption password out of ``file_name``.

    This deliberately lives in ``cli()`` rather than ``main()``: the GUI
    calls ``main(["-p", <the password itself>, ...])`` straight from its
    entry box, so ``main`` has to keep treating that argument as a literal
    password. Only the command line names a *file* there. (``-k``/``-l`` are
    read inside ``main`` because the GUI passes paths for those too.)

    A trailing newline is nearly always an editor artefact rather than part
    of the password, and keeping it fails deep inside the decryptor with an
    opaque "invalid padding byte" error, so strip it. Only CR/LF is removed
    -- spaces and tabs could legitimately end a password.
    """
    return util._binary_contents_of(file_name).rstrip(b'\r\n')


def main(args):
    # NB: for "-p", args[1] is the password itself, not a path -- see
    # _password_from_file above.
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

    if os.path.isfile(ff):
        _check_not_ecryptfs(ff)

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
                # Skip macOS / filesystem metadata that isn't a Synology
                # encrypted file. Otherwise the decryptor explodes on
                # garbage input.
                if filename in (".DS_Store", "Thumbs.db") or filename.startswith("._"):
                    continue
                _check_not_ecryptfs(filename)
                decrypt_args.append((
                    os.path.join(input_dir, filename),
                    os.path.join(input_dir.replace(ff, output_dir, 1), filename),
                    password,
                    private_key,
                    public_key,
                ))

        # ThreadPool (not Pool) so we get parallelism without spawning new
        # processes — critical inside a py2app bundle where re-execing the
        # main app binary would relaunch the GUI. AES (pycryptodomex) and
        # lz4 (lz4.frame) both release the GIL in their C extensions, so
        # threads parallelise the actual work just fine.
        with ThreadPool() as p:
            p.starmap(files.decrypt_file, decrypt_args)

    else:
        files.decrypt_file(ff, os.path.join(output_dir, fp), password=password, private_key=private_key, public_key=public_key)


def cli():
    """Console-script entry point installed via ``[project.scripts]``.
    Parses argv via docopt (per the module docstring) and forwards to
    ``main`` in the positional shape it expects."""
    arguments = docopt.docopt(__doc__)
    out = arguments['--output-directory']
    encrypted_files = arguments['<encrypted-file>']
    if arguments['--password-file']:
        argv = ['-p', _password_from_file(arguments['--password-file']), out]
    else:
        argv = ['-k', arguments['--private-key-file'],
                arguments['--public-key-file'], out]
    for f in encrypted_files:
        main(argv + [f])


if __name__ == '__main__':
    cli()
