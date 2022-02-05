"""synology-decrypt"""
import logging
import sys
from multiprocessing import Pool
from pathlib import Path

from syndecrypt import files
from syndecrypt import util


def decrypt(args):
    """
    Decrypt a file.
        args: list of arguments.

    Usage:
      syndecrypt (-p <password> <output dir> <source>) |
                 (-k <privkeyfile> <pubkeyfile> <output_dir> <source>)
      syndecrypt (-h | --help)

    source:         Can be an encrypted file or a directory with encrypted
                    file. If source is a relative path, the path will be
                    included when restoring files in output_dir.
    output_dir:     The directory where files are restored. If source is a
                    directory, then the directory structure of source is
                    recreated in output_dir.
    password:       the password to decrypt the files with
    pubkeyfile:     The public key file for decryption
                    (not needed when using password)
    privkeyfile:    The private key file for decryption
                    (not needed with password)
    """

    if "-h" in args:
        print(decrypt.__doc__)

        return

    if args[0] == "-p":
        arguments = {
            "--password-file": args[1],
            "--private-key-file": None,
            "--public-key-file": None,
            "--output-directory": args[2],
            "<encrypted-file>": args[3],
        }
    elif args[0] == "-k":
        arguments = {
            "--password-file": None,
            "--private-key-file": args[1],
            "--public-key-file": args[2],
            "--output-directory": args[3],
            "<encrypted-file>": args[4],
        }

    password_file_name = arguments["--password-file"]

    if password_file_name is not None:
        password = arguments["--password-file"]
    else:
        password = None

    private_key_file_name = arguments["--private-key-file"]

    if private_key_file_name is not None:
        private_key = util._binary_contents_of(private_key_file_name)
    else:
        private_key = None

    public_key_file_name = arguments["--public-key-file"]

    if public_key_file_name is not None:
        public_key = util._binary_contents_of(public_key_file_name)
    else:
        public_key = None

    output_dir = arguments["--output-directory"]
    output_dir = Path(output_dir).resolve()

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    logging.basicConfig(format="%(levelname)s: %(message)s")

    source = Path(arguments["<encrypted-file>"])
    source_abs = source.resolve()

    if source != source_abs:
        # Dealing with a relative path. Restoring it in the destination

        if source.is_dir():
            output_dir = output_dir / source
        else:
            output_dir = output_dir / source.parents[0]

        output_dir.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        decrypt_args = []

        for source2 in source.glob("**/*"):
            if source2.is_file():
                fout_dir = output_dir / source2.relative_to(source).parents[0]
                fout_dir.mkdir(parents=True, exist_ok=True)

                sig = source2.resolve().open("rb").read(17)

                if sig != b"__CLOUDSYNC_ENC__":
                    log.warning("%s is not an encrypted file", source2)

                    continue

                decrypt_args.append(
                    (
                        source2.resolve(),
                        fout_dir / source2.name,
                        password,
                        private_key,
                        public_key,
                    )
                )

        with Pool() as pool:
            pool.starmap(files.decrypt_file, decrypt_args)

    else:
        files.decrypt_file(
            source.resolve(),
            output_dir / source.name,
            password=password,
            private_key=private_key,
            public_key=public_key,
        )


def __main__():
    decrypt(sys.argv[1:])


if __name__ == "__main__":
    decrypt(sys.argv[1:])
