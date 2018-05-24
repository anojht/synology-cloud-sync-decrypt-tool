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
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


from subprocess import Popen, PIPE
import threading

class FilterSubprocess:
        """
        A wrapper around Popen(stdin=PIPE,stdout=PIPE) where stdout
        is sent to the provided callback handler.
        """

        def __init__(self, command_line, stdout_handler):
                self.stdout_handler = stdout_handler
                self.proc = Popen(args=command_line, stdin=PIPE, stdout=PIPE)
                self.stdout_handler_thread = threading.Thread(target=self.stdout_handler_loop)
                self.stdout_handler_thread.start()

        def __enter__(self):
                return self

        def __exit__(self, exc_type, exc_value, traceback):
                self.close()

        def stdout_handler_loop(self):
                while True:
                        c = self.proc.stdout.read(1024)
                        if len(c) == 0: break
                        self.stdout_handler(c)

        def write(self, b):
                self.proc.stdin.write(b)

        def close(self):
                self.proc.stdin.close()
                self.stdout_handler_thread.join()


class Lz4Decompressor(FilterSubprocess):
        def __init__(self, decompressed_chunk_handler):
                FilterSubprocess.__init__(self, ['lz4', '-d'], stdout_handler=decompressed_chunk_handler)
