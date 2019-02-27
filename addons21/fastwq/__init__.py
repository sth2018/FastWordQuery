# -*- coding:utf-8 -*-
#
# Copyright (C) 2018 sthoo <sth201807@gmail.com>
#
# Support: Report an issue at https://github.com/sth2018/FastWordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import ssl
import sys

from anki.hooks import addHook
from anki.utils import isMac

sys.dont_write_bytecode = True
if isMac:
    ssl._create_default_https_context = ssl._create_unverified_context

############## other config here ##################
shortcut = ('Ctrl+Alt' if isMac else 'Ctrl') + '+Q'

###################################################


def start_here():
    from . import common as fastwq
    from .context import config
    config.read()
    fastwq.my_shortcut = shortcut
    if not fastwq.have_setup:
        fastwq.have_setup = True
        fastwq.config_menu()
        fastwq.browser_menu()
        fastwq.context_menu()
        fastwq.customize_addcards()


addHook("profileLoaded", start_here)
