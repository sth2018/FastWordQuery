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

import time
from collections import defaultdict

from aqt.qt import *

from ..context import APP_ICON
from ..lang import _

__all__ = ['ProgressWindow']

_INFO_TEMPLATE = u''.join([
    u'<strong>' + _('QUERIED') + u'</strong>',
    u'<p>' + 45 * u'-' + u'</p>',
    u'<p>' + _('SUCCESS') + u' <b>{}</b> ' + _('WORDS') + u'</p>',
    u'<p>' + _('SKIPED') + u' <b>{}</b> ' + _('WORDS') + u'</p>',
    u'<p>' + _('UPDATE') + u' <b>{}</b> ' + _('FIELDS') + u'</p>',
    u'<p>' + _('FAILURE') + u' <b>{}</b> ' + _('WORDS') + u'</p>',
])


class ProgressWindow(object):
    """
    Query progress window
    """

    def __init__(self, mw):
        self.mw = mw
        self.app = QApplication.instance()
        self._win = None
        self._msg_count = defaultdict(int)
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
            self._msg_count.get('skips_number', 0))
        number_info = _INFO_TEMPLATE.format(words_number, skips_number,
                                            fields_number, fails_number)
        self._update(
            label=number_info,
            value=words_number + skips_number + fails_number)
        self._win.adjustSize()
        self.app.processEvents()

    def update_title(self, title):
        if self.abort():
            return
        self._win.setWindowTitle(title)

    def start(self, max=0, min=0, label=None, parent=None):
        self._msg_count.clear()
        # setup window
        label = label or _("Processing...")
        parent = parent or self.app.activeWindow() or self.mw
        self._win = QProgressDialog(label, '', min, max, parent)
        self._win.setWindowModality(Qt.ApplicationModal)
        self._win.setCancelButton(None)
        self._win.canceled.connect(self.finish)
        self._win.setWindowTitle("FastWQ - Querying...")
        self._win.setModal(True)
        self._win.setWindowFlags(
            self._win.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._win.setWindowIcon(APP_ICON)
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
            self.app.processEvents(QEventLoop.ExcludeUserInputEvents)
            self._last_update = time.time()

    def _set_busy(self):
        self._disabled = True
        self.mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))

    def _unset_busy(self):
        self._disabled = False
        self.app.restoreOverrideCursor()
