##############################################################################
##                                                                          ##
## snimpy -- Interactive SNMP tool                                          ##
##                                                                          ##
## Copyright (C) Vincent Bernat <bernat@luffy.cx>                           ##
##                                                                          ##
## Permission to use, copy, modify, and distribute this software for any    ##
## purpose with or without fee is hereby granted, provided that the above   ##
## copyright notice and this permission notice appear in all copies.        ##
##                                                                          ##
## THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES ##
## WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         ##
## MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  ##
## ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   ##
## WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    ##
## ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  ##
## OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           ##
##                                                                          ##
##############################################################################

# We are using readline module of Python. Depending on the Python
# distribution, this module may be linked to GNU Readline which is
# GPLv2 licensed.

"""Provide an interactive shell for snimpy.

The main method is C{interact()}. It will either use IPython if
available or just plain python Shell otherwise. It will also try to
use readline if available.

For IPython, there is some configuration stuff to use a special
profile. This is the recommended way to use it. It allows a separate
history.
"""

import sys
import os
import atexit
import code
from datetime import timedelta
try:
    import rlcompleter
    import readline
except ImportError:
    readline = None
try:
    from IPython.Shell import IPShellEmbed
except ImportError:
    IPShellEmbed = None

import manager
from config import conf
from version import VERSION

def write_history_file():
    if readline and conf.histfile:
        try:
            readline.write_history_file(os.path.expanduser(conf.histfile))
        except IOError,e:
            pass

def interact():
    banner  = "\033[1mSnimpy\033[0m (%s) -- An interactive SNMP tool.\n" % VERSION
    banner += "  load        -> load an additional MIB\n"
    banner += "  M           -> manager object"

    local = { "conf": conf,
              "M": manager.Manager,
              "load": manager.load,
              "timedelta": timedelta,
              "snmp": manager.snmp
              }

    if len(sys.argv) <= 1:
        manager.Manager._complete = True

    for ms in conf.mibs:
        manager.load(ms)

    globals().update(local)

    if len(sys.argv) > 1:
        sys.argv = sys.argv[1:]
        execfile(sys.argv[0], local)
        return

    if IPShellEmbed and conf.ipython:
        argv = ["-prompt_in1", "Snimpy [\\#]> ",
                "-prompt_out", "Snimpy [\\#]: "]
        if conf.ipythonprofile:
            argv += ["-profile", conf.ipythonprofile]
        shell = IPShellEmbed(argv=argv,
                             banner=banner, user_ns=local)
        shell.IP.InteractiveTB.tb_offset += 1 # Not interested by traceback in this module
        shell()
    else:
        if readline:
            if conf.histfile:
                try:
                    readline.read_history_file(os.path.expanduser(conf.histfile))
                except IOError:
                    pass
                atexit.register(write_history_file)

            readline.set_completer(rlcompleter.Completer(local).complete)
            readline.parse_and_bind("tab: menu-complete")
        sys.ps1 = conf.prompt
        code.interact(banner=banner, local=local)
