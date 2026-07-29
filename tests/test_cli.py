"""Tests for the ``syndecrypt`` console-script entry point.

The CLI layer had no coverage at all, which is how ``-p`` came to disagree
with its own ``--help`` text for two releases: the flag is documented as
taking a *file* containing the password, but the value was being used
verbatim as the password itself.
"""
from __future__ import print_function

import sys

import syndecrypt.__main__ as main_module
import syndecrypt.util as util

PASSWORD_FILE = 'tests/testfiles-secrets/password.txt'
PRIVATE_KEY_FILE = 'tests/testfiles-secrets/private.pem'
PUBLIC_KEY_FILE = 'tests/testfiles-secrets/public.pem'
ENCRYPTED_FILE = 'tests/testfiles-csenc/single-line.txt'

PLAINTEXT = b'Just a single line, no newline character at the end...'


def _run_cli(monkeypatch, argv):
    monkeypatch.setattr(sys, 'argv', ['syndecrypt'] + argv)
    main_module.cli()


def test_cli_reads_password_from_file(tmp_path, monkeypatch):
    """-p names a file, per the usage string, not the password itself."""
    _run_cli(monkeypatch, ['-p', PASSWORD_FILE, '-O', str(tmp_path), ENCRYPTED_FILE])
    assert (tmp_path / 'single-line.txt').read_bytes() == PLAINTEXT


def test_cli_password_file_trailing_newline_is_ignored(tmp_path, monkeypatch):
    """An editor-added trailing newline must not change the password.

    Without stripping, this fails inside the decryptor with an opaque
    "invalid padding byte" error rather than anything actionable.
    """
    password_file = tmp_path / 'password-with-newline.txt'
    password_file.write_bytes(util._binary_contents_of(PASSWORD_FILE) + b'\n')

    output_dir = tmp_path / 'out'
    output_dir.mkdir()
    _run_cli(monkeypatch, ['-p', str(password_file), '-O', str(output_dir), ENCRYPTED_FILE])
    assert (output_dir / 'single-line.txt').read_bytes() == PLAINTEXT


def test_cli_reads_private_and_public_key_files(tmp_path, monkeypatch):
    _run_cli(monkeypatch, ['-k', PRIVATE_KEY_FILE, '-l', PUBLIC_KEY_FILE,
                           '-O', str(tmp_path), ENCRYPTED_FILE])
    assert (tmp_path / 'single-line.txt').read_bytes() == PLAINTEXT


def test_main_takes_a_literal_password(tmp_path):
    """The GUI calls main() with the password straight from its entry box.

    Pinning this stops a well-meaning change to main() -- making it read a
    file, symmetrically with -k/-l -- from silently breaking the GUI, which
    has no test coverage of its own.
    """
    password = util._binary_contents_of(PASSWORD_FILE).decode('ascii')
    main_module.main(['-p', password, str(tmp_path), ENCRYPTED_FILE])
    assert (tmp_path / 'single-line.txt').read_bytes() == PLAINTEXT
