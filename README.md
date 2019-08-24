# Synology Cloud Sync Decryption Tool
Open source version of the Synology Cloud Sync decryption tool with a nice GUI option for MacOS and Linux!

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

Install on Mac:

```
Please note that the app found in the release is set to auto install the necessary dependencies. This is for the average user who may not be savvy or not want to install brew on their mac. If you for some reason do not trust the lz4 binary and Xcode Command Line Tools installer packaged with the app, you can clone the repo, remove the InstallMeFirst.app and follow the instructions below.
brew install lz4
brew install python
# check python 3
python3 -v
python3 -m venv ~/syndecrypt-venv
source ~/syndecrypt-venv/bin/activate
pip install -r syndecrypt/requirements.txt
python Synology.py
```

For Installation on Linux:
```
Install lz4 from your package manager repository
For Ubuntu:
apt-get install lz4
For Fedora:
dnf install lz4

Determine the location of lz4:
which lz4
/usr/bin/lz4 is the default location in Fedora

For this package to work, you will need to make a symlink for /usr/bin/lz4 to /usr/local/bin/lz4
ln -s /usr/bin/lz4 /usr/local/bin/lz4
You can also change the path inside the Synology.py file if you do not want to do the symlink

Install tkinter (UI framework for the project)
For Ubuntu:
apt-get install python3-tk
For Fedora:
dnf install python3-tkinter

Setup python environment:
python3 -m venv ~/syndecrypt-venv
source ~/syndecrypt-venv/bin/activate
pip install -r syndecrypt/requirements.txt
python Synology.py
```

## Troubleshooting Installation Errors

If you choose to install dependencies manually as per the instructions above, you may need to build some dependencies from source. If `pip install` is dying with clang errors during this process, try following these steps:

1. Identify which dependency is failing or missing, such as `libgmp`.
2. Ensure you have a suitable copy of the dependency, such as with Homebrew (e.g. `brew install gmp`).
3. Identify where Homebrew installs the headers and libraries (usually `/usr/local/include` and `/usr/local/lib`, respectively).
4. Provide pip with arguments to pass to clang specifying these paths.
    - [Using ~/.pydistutils.cfg](https://stackoverflow.com/a/19253719)
    - [Using `--global-option`](https://stackoverflow.com/a/28981343)

## Troubleshooting App Issues

The app is set to create DEBUG logs in the following location: `~/Library/Logs/com.anojht.opensourcesynologycloudsyncdecrypttool.log or ~/com.anojht.opensourcesynologycloudsyncdecyrpttool.log in the case of Linux.`

If you require help please include your log file when creating issues in this repository.

# Feedback

Feel very free to create a GitHub issue, create a pull request, or drop me a
line, if you have any opinions, bug reports, requests, or whatever about this
project.  Thanks!

# License

The code in this repository is licensed under the GPLv3; see LICENSE.txt for
details.

# Information Sources

There are four pieces of information from Synology, unfortunately spread out
over multiple places which are not easy to find, and not linked together at
all:

 * 'Synology Cloud Sync Decryption Tool', the closed source decryption tool
   (Windows and Linux only, apparently GUI only) which Synology provides.

   It can be obtained through the Synology Support Download Center at
   https://www.synology.com/en-us/support/download/, then choose a NAS that
   offers Cloud Sync (many of them, e.g.,
   [DS110j](https://www.synology.com/en-us/support/download/DS110j)).

   As of this writing the current version is 013.

   (The GUI has a help icon that opens
   https://help.synology.com/enu/utility/SynologyCloudSyncDecryptionTool which
   which contains the same infor as the KB article below.  It also returns
   404 fairly often.)
   
 * Synology Knowledge Base article ["What is Synology Cloud Sync Decryption
   Tool?"](https://www.synology.com/en-global/knowledgebase/DSM/tutorial/Application/What_is_Synology_Cloud_Sync_Decryption_Tool)
   describing how to use the above decryption tool.

 * Page 9 of ["Cloud Sync White Paper -- Based on DSM
   6.0"](https://global.download.synology.com/download/Document/WhitePaper/Synology_Cloud_Sync_White_Paper-Based_on_DSM_6.0.pdf)
([archive.org copy](https://web.archive.org/web/20160606190954/https://global.download.synology.com/download/Document/WhitePaper/Synology_Cloud_Sync_White_Paper-Based_on_DSM_6.0.pdf))
   which I received through Synology Support.

 * The Synology NAS software just lets me check an 'encrypt' checkbox and asks
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

The current code is still basic and does not provide enough explanation yet.  I'd still like to do the following:

## Core decryption algorithm

* ~~Support new file format 3.0.~~
* ~~Investigate what key2_hash is a hash of.~~
* ~~Warn for any known field that is missing, and for every unknown field.~~
* Rename `core` to `algorithm`?
* Full documentation of the algorithm in the 'core' module.
* Add algorithm diagram.
* Support `encrypt` = 0 and `compress` = 0 modes.  (It is an error if either of these fields is not specified.)
* Add verification of `@SynologyCloudSync/cloudsync_encrypt.info` file using password and/or private key.
* Investigate how DSM GUI handles non-ASCII passwords.

## Command-line decryption tool

* ~~Decrypt directories recursively.~~
* Check password file: check single line, warning if not printable ASCII.
* Make log level configurable (default: warning).
* Add `--verify` option, to check decryptability and file structure.
* Make `--verify` option also verify `@SynologyCloudSync/cloudsync_encrypt.info` files.

## Encryption

* Add encryption option/algorithm.

## Open source work used

* Original command line decryption tool project located [here](https://github.com/marnix/synology-decrypt) 
