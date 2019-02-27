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

import sys

from anki.utils import isMac
from aqt.qt import *

from ..context import APP_ICON

__all__ = ['Dialog', 'WIDGET_SIZE']


class Dialog(QDialog):
    '''
    Base used for all dialog windows.
    '''

    def __init__(self, parent, title):
        '''
        Set the modal status for the dialog, sets its layout to the
        return value of the _ui() method, and sets a default title.
        '''

        self._title = title if "FastWQ" in title else "FastWQ - " + title
        self._parent = parent
        super(Dialog, self).__init__(parent)

        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(APP_ICON)
        self.setWindowTitle(self._title)
        # 2 & 3 & mac compatible
        if isMac and sys.hexversion >= 0x03000000:
            QApplication.setStyle('Fusion')


class WidgetSize(object):
    '''
    constant values
    '''
    dialog_width = 850
    dialog_height_margin = 166 if isMac and sys.hexversion < 0x03000000 else 146
    map_min_height = 0
    map_max_height = 30
    map_fld_width = 100
    map_dictname_width = 150
    map_dict_width = 160
    map_field_width = 200


WIDGET_SIZE = WidgetSize()
