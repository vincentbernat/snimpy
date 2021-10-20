#
# snimpy -- Interactive SNMP tool
#
# Copyright (C) Vincent Bernat <bernat@luffy.cx>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import os.path
import importlib


class Conf:
    prompt = "\033[1m[snimpy]>\033[0m "
    histfile = "~/.snimpy_history"  # Not used with IPython
    userconf = "~/.snimpy.conf"
    ipython = True
    ipythonprofile = None  # Set for example to "snimpy"
    mibs = []

    def load(self, userconf=None):
        if userconf is None:
            userconf = self.userconf
        loader = importlib.machinery.SourceFileLoader(
            'confuser',
            os.path.expanduser(userconf))
        spec = importlib.util.spec_from_loader('confuser', loader)
        if spec is not None:
            try:
                confuser = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(confuser)
            except FileNotFoundError:
                pass
            else:
                for k in confuser.__dict__:
                    if not k.startswith("__"):
                        setattr(self, k, confuser.__dict__[k])

        return self
