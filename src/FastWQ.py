#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 ST.Huang <wenhonghuang@gmail.com>
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

def start_here():

    """
    Copyright © 2016–2017 ST.Huang <wenhonghuang@gmail.com>
    Support: Report an issue at https://github.com/sth2018/FastWordQuery/issues
    """

    import fastwq

    ############## other config here ##################
    # shortcut
    shortcut = 'Ctrl+Q'
    ###################################################

    fastwq.config.read()
    if not fastwq.have_setup:
        fastwq.config_menu()
        fastwq.browser_menu()
        fastwq.customize_addcards()
    fastwq.window_shortcut(shortcut)

addHook("profileLoaded", start_here)
