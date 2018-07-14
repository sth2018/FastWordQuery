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
        # we need to manually manage minimum time to show, as qt gets confused
        # by the db handler
        # self._win.setMinimumDuration(100000)
        self._counter = min
        self._min = min
        self._max = max
        self._firstTime = time.time()
        self._lastUpdate = time.time()
        self._disabled = False
        self._win.show()
        self.app.processEvents()

    def abort(self):
        # self.aborted = True
        return self._win.wasCanceled()

    def finish(self):
        self._win.hide()
        self._unsetBusy()
        self._win.destroy()

    def _update(self, label=None, value=None, process=True, maybeShow=True):
        elapsed = time.time() - self._lastUpdate
        if label:
            self._win.setLabelText(label)
        if self._max:
            self._counter = value or (self._counter + 1)
            self._win.setValue(self._counter)
        if process and elapsed >= 0.2:
            self.app.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
            self._lastUpdate = time.time()

    def _setBusy(self):
        self._disabled = True
        self.mw.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

    def _unsetBusy(self):
        self._disabled = False
        self.app.restoreOverrideCursor()
