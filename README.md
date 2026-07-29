[![Tests](https://img.shields.io/github/actions/workflow/status/anojht/synology-cloud-sync-decrypt-tool/tests.yml?branch=master&label=tests)](https://github.com/anojht/synology-cloud-sync-decrypt-tool/actions/workflows/tests.yml)
[![Github All Releases](https://img.shields.io/github/downloads/anojht/synology-cloud-sync-decrypt-tool/total.svg)](https://github.com/anojht/synology-cloud-sync-decrypt-tool)
[![Paypal](https://img.shields.io/badge/paypal-donate-yellow.svg)](https://paypal.me/Anojh)

---

# Synology Cloud Sync Decryption Tool

Open source version of the Synology Cloud Sync decryption tool with a nice GUI option for MacOS and Linux!

## Open source work used

- Original command line decryption tool project located [here](https://github.com/marnix/synology-decrypt)
- Without the work of the original author @marnix, the GUI version of this tool would not exist.

# Goal

Currently, Synology has this tool available for Windows and Ubuntu/Fedora but not on mac and the tool is closed source.
I want to create an open source implementation/description of the encryption/decryption
algorithm used by Synology NAS products in their Cloud Sync feature, where one
can sync data on the NAS to the likes of Google Drive.

Synology publishes a closed source tool (see below), but I would like to be
know how to decrypt my own data with my own password or private key, in the
(unlikely) event that I lose access to both a NAS of this type and the closed
source tool.

Official documentation of the encryption algorithm exists, but only on a high
level, and the file format is not documented at all.

I've chosen Python, since I think that allows to to express the algorithm most
clearly.

(Please note that I explicitly do not want to reverse engineer the closed
source 'Synology Cloud Sync Decryption Tool', since I want to avoid doing
things that might be construed to be illegal.)

# Install

## Use the prebuilt macOS app

Download the latest `.app` from the [Releases](https://github.com/anojht/synology-cloud-sync-decrypt-tool/releases) page, drag it to `/Applications`, and run it. Apple Silicon (M1/M2/M3) and Intel are both supported. No external dependencies, everything is bundled.

## Run from source

Requires [`uv`](https://github.com/astral-sh/uv) (`brew install uv`) and `make`.

```bash
git clone https://github.com/anojht/synology-cloud-sync-decrypt-tool.git
cd synology-cloud-sync-decrypt-tool
make sync
make run
```

`uv` provisions Python 3.13, creates an isolated `.venv/`, and installs all dependencies (including `lz4`, `Pillow`, `pycryptodomex`).

## Run tests

```bash
make test
```

## Build the macOS app yourself

The build is driven by `make` (run `make help` to see every target).

### Build for the architecture you're on

```bash
make build-arm64    # Apple Silicon (M1 / M2 / M3)
make build-x86_64   # Intel (or Apple Silicon under Rosetta 2)
```

The output is at `dist/Open Source Synology Cloud Sync Decryption Tool.app`. Verify the architecture with:

```bash
file "dist/Open Source Synology Cloud Sync Decryption Tool.app/Contents/MacOS/Open Source Synology Cloud Sync Decryption Tool"
```

> **Building x86_64 on Apple Silicon** requires Rosetta 2:
>
> ```bash
> softwareupdate --install-rosetta --agree-to-license
> ```

### Build a release for both architectures

`make dist-all` builds both architectures back-to-back and produces ready-to-publish zips in `dist-zips/`:

```bash
make dist-all
# →  dist-zips/Open Source Synology Cloud Sync Decryption Tool-arm64.zip
#    dist-zips/Open Source Synology Cloud Sync Decryption Tool-x86_64.zip
```

Each `make build-*` and `make dist-*` invocation wipes `.venv/` and `dist/` so the build environment matches the target architecture (uv pulls per-arch wheels for `lz4`, `Pillow`, and `pycryptodomex`).

## Troubleshooting App Issues

The app is set to create DEBUG logs in the following location: `~/synologycloudsyncdecrypttool.log`

If you require help please include your log file when creating issues in this repository.

# Feedback

Feel very free to create a GitHub issue, create a pull request, or drop me a
line, if you have any opinions, bug reports, requests, or whatever about this
project. Thanks!

# License

The code in this repository is licensed under the GPLv3; see LICENSE.txt for
details.

# Information Sources

There are four pieces of information from Synology, unfortunately spread out
over multiple places which are not easy to find, and not linked together at
all:

- 'Synology Cloud Sync Decryption Tool', the closed source decryption tool
  (Windows and Linux only, apparently GUI only) which Synology provides.

  It can be obtained through the Synology Support Download Center at
  https://www.synology.com/en-us/support/download/, then choose a NAS that
  offers Cloud Sync (many of them, e.g.,
  [DS110j](https://www.synology.com/en-us/support/download/DS110j)).

  As of this writing the current version is 013.

  (The GUI has a help icon that opens
  https://help.synology.com/enu/utility/SynologyCloudSyncDecryptionTool which
  which contains the same infor as the KB article below. It also returns
  404 fairly often.)

- Synology Knowledge Base article ["What is Synology Cloud Sync Decryption
  Tool?"](https://www.synology.com/en-global/knowledgebase/DSM/tutorial/Application/What_is_Synology_Cloud_Sync_Decryption_Tool)
  describing how to use the above decryption tool.

- Page 9 of ["Cloud Sync White Paper -- Based on DSM
  6.0"](https://global.download.synology.com/download/Document/WhitePaper/Synology_Cloud_Sync_White_Paper-Based_on_DSM_6.0.pdf)
  ([archive.org copy](https://web.archive.org/web/20160606190954/https://global.download.synology.com/download/Document/WhitePaper/Synology_Cloud_Sync_White_Paper-Based_on_DSM_6.0.pdf))
  which I received through Synology Support.

- The Synology NAS software just lets me check an 'encrypt' checkbox and asks
  for a password, and then sends back a zip-file `key.zip` with files
  `public.pem` and `private.pem`, without any explanation what I can/should do
  with it.

  The above documents make it clear that the files are encrypted individually,
  and that each file can be decrypted using only the password or only
  `private.pem`.

Until now, there is only one unofficial source of information:

- The answers and comments on this StackOverflow question: [What decryption algorithm is
  used here?](http://security.stackexchange.com/q/124838/3617).

# To Do

The current code is still basic and does not provide enough explanation yet. I'd still like to do the following:

## Core decryption algorithm

- ~~Support new file format 3.0.~~
- ~~Investigate what key2_hash is a hash of.~~
- ~~Warn for any known field that is missing, and for every unknown field.~~
- Rename `core` to `algorithm`?
- Full documentation of the algorithm in the 'core' module.
- Add algorithm diagram.
- Support `encrypt` = 0 and `compress` = 0 modes. (It is an error if either of these fields is not specified.)
- Add verification of `@SynologyCloudSync/cloudsync_encrypt.info` file using password and/or private key.
- Investigate how DSM GUI handles non-ASCII passwords.

## Command-line decryption tool

- ~~Decrypt directories recursively.~~
- Check password file: check single line, warning if not printable ASCII.
- Make log level configurable (default: warning).
- Add `--verify` option, to check decryptability and file structure.
- Make `--verify` option also verify `@SynologyCloudSync/cloudsync_encrypt.info` files.

## Encryption

- Add encryption option/algorithm.
