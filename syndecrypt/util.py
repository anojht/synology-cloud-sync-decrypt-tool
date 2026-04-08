import logging

LOGGER=logging.getLogger(__name__)

def _binary_contents_of(file_name):
        with open(file_name, 'rb') as f: return f.read()


# From http://code.activestate.com/recipes/410692/
# "Readable switch construction without lambdas or dictionaries"

# This class provides the functionality we want. You only need to look at
# this if you want to know how this works. It only needs to be defined
# once, no need to muck around with its internals.
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


import lz4.frame


class Lz4Decompressor:
        """
        Streaming lz4 frame decompressor with the same interface the rest of
        the code expects: use as a context manager, call ``write(bytes)`` to
        feed compressed input, and any decompressed output is forwarded to
        ``decompressed_chunk_handler``.
        """

        def __init__(self, decompressed_chunk_handler):
                self.stdout_handler = decompressed_chunk_handler
                self._ctx = lz4.frame.LZ4FrameDecompressor()

        def __enter__(self):
                return self

        def __exit__(self, exc_type, exc_value, traceback):
                pass

        def write(self, b):
                if not b:
                        return
                out = self._ctx.decompress(b)
                if out:
                        self.stdout_handler(out)


