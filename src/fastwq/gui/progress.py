#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 sthoo <sth201807@gmail.com>
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


import time
from collections import defaultdict

from PyQt4 import QtCore, QtGui
from ..lang import _


__all__ = ['ProgressWindow']


_INFO_TEMPLATE = u''.join([
    _('QUERIED') + u'<br>' + 45 * u'-' + u'<br>',
    _('SUCCESS') + u' {} ' + _('WORDS') + u'<br>',
    _('SKIPED') + u' {} ' + _('WORDS') + u'<br>',
    _('UPDATE') + u' {} ' +  _('FIELDS') + u'<br>',
    _('FAILURE') + u' {} ' + _('WORDS') + u''
])


class ProgressWindow(object):
    """
    Query progress window
    """

    def __init__(self, mw):
        self.mw = mw
        self.app = QtGui.QApplication.instance()
        self._win = None
        self._msg_count = defaultdict(int)
        self._last_number_info = u''
        self._last_update = 0
        self._first_time = 0
        self._disabled = False

    def update_labels(self, data):
        if self.abort():
            return

        if data.type == 'count':
            self._msg_count.update(data)
        else:
            return

        words_number, fields_number, fails_number, skips_number = (
            self._msg_count.get('words_number', 0),
            self._msg_count.get('fields_number', 0),
            self._msg_count.get('fails_number', 0),
            self._msg_count.get('skips_number', 0)
        )
        number_info = _INFO_TEMPLATE.format(
            words_number,
            skips_number,
            fields_number,
            fails_number
        )

        if self._last_number_info == number_info:
            return
        
        self._last_number_info = number_info
        self._update(label=number_info, value=words_number+skips_number+fails_number)
        self._win.adjustSize()

    def update_title(self, title):
        if self.abort():
            return
        self._win.setWindowTitle(title)

    def start(self, max=0, min=0, label=None, parent=None):
        self._msg_count.clear()
        # setup window
        label = label or _("Processing...")
        parent = parent or self.app.activeWindow() or self.mw
        self._win = QtGui.QProgressDialog(label, '', min, max, parent)
        self._win.setWindowModality(QtCore.Qt.ApplicationModal)
        self._win.setCancelButton(None)
        self._win.canceled.connect(self.finish)
        self._win.setWindowTitle("Querying...")
        self._win.setAutoReset(True)
        self._win.setAutoClose(True)
        self._win.setMinimum(0)
        self._win.setMaximum(max)
        # we need to manually manage minimum time to show, as qt gets confused
        # by the db handler
        # self._win.setMinimumDuration(100000)
        self._first_time = time.time()
        self._last_update = time.time()
        self._disabled = False
        self._win.show()
        self._win.setValue(0)
        self.app.processEvents()

    def abort(self):
        # self.aborted = True
        return self._win.wasCanceled()

    def finish(self):
        self._win.hide()
        self._unset_busy()
        self._win.destroy()

    def _update(self, label, value, process=True):
        elapsed = time.time() - self._last_update
        if label:
            self._win.setLabelText(label)
        if value:
            self._win.setValue(value)
        if process and elapsed >= 0.2:
            self.app.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
            self._last_update = time.time()

    def _set_busy(self):
        self._disabled = True
        self.mw.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

    def _unset_busy(self):
        self._disabled = False
        self.app.restoreOverrideCursor()
