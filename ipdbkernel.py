#!/usr/bin/env python

"""
IPython debugger Jupyter kernel.
"""

import bdb
import functools
import sys

from ipykernel.kernelbase import Kernel
from IPython.core.debugger import Pdb, BdbQuit_excepthook, BdbQuit_IPython_excepthook
from IPython.terminal.ipapp import TerminalIPythonApp

class PhonyStdout(object):
    def __init__(self, write_func):
        self._write_func = write_func
    def flush(self):
        pass
    def write(self, s):
        self._write_func(s)
    def close(self):
        pass

class IPdbKernel(Kernel):
    implementation = 'IPdbKernel'
    implementation_version = '0.1'
    language = 'IPdb'
    language_version = '0.1'
    language_info = {'mimetype': 'text/plain'}
    banner = "IPython debugger kernel"

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)

        # Instantiate IPython.core.debugger.Pdb here, pass it a phony 
        # stdout that provides a dummy flush() method and a write() method
        # that internally sends data using a function so that it can
        # be initialized to use self.send_response()
        write_func = lambda s: self.send_response(self.iopub_socket,
                                                  'stream',
                                                  {'name': 'stdout',
                                                   'text': s})
        sys.excepthook = functools.partial(BdbQuit_excepthook,
                                           excepthook=sys.excepthook)
        self.debugger = Pdb(stdout=PhonyStdout(write_func))
        self.debugger.set_trace(sys._getframe().f_back)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        # Process command:
        line = self.debugger.precmd(code)
        stop = self.debugger.onecmd(line)
        stop = self.debugger.postcmd(stop, line)
        if stop:
            self.debugger.postloop()

        return {'status': 'ok', 'execution_count': self.execution_count,
                'payload': [], 'user_expression': {}}

    def do_complete(self, code, cursor_pos):
        code = code[:cursor_pos]

        default = {'matches': [], 'cursor_start': 0,
                   'cursor_end': cursor_pos, 'metadata': dict(),
                   'status': 'ok'}

        if not code or code[-1] == ' ':
            return default

        # Run Pdb.completenames on code, extend matches with results:
        matches = self.debugger.completenames(code)

        if not matches:
            return default

        return {'matches': sorted(matches), 'cursor_start': cursor_pos-len(code),
                'cursor_end': cursor_pos, 'metadata': dict(),
                'status': 'ok'}

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=IPdbKernel)

