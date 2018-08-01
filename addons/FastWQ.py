#-*- coding:utf-8 -*-
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

from anki.hooks import addHook

############## other config here ##################
shortcut = 'Ctrl+Q'
LDOCE6_PATH = u'D:\\mdx_server\\mdx\\LDOCE6.mdx'
###################################################

def start_here():

    """
    Copyright (C) 2018 sthoo <sth201807@gmail.com>
    Support: Report an issue at https://github.com/sth2018/FastWordQuery/issues
    """

    import fastwq

    fastwq.config.read()
    fastwq.config.LDOCE6_PATH = LDOCE6_PATH
    fastwq.my_shortcut = shortcut
    if not fastwq.have_setup:
        fastwq.have_setup = True
        fastwq.config_menu()
        fastwq.browser_menu()
        fastwq.customize_addcards()
        if fastwq.config.auto_update:
            fastwq.check_updates(True)

addHook("profileLoaded", start_here)
