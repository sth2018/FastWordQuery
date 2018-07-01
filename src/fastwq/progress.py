# Copyright: Damien Elmes <anki@ichi2.net>
# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import time
from collections import defaultdict

from aqt.qt import *
from .lang import _


# fixme: if mw->subwindow opens a progress dialog with mw as the parent, mw
# gets raised on finish on compiz. perhaps we should be using the progress
# dialog as the parent?

# Progress info
##########################################################################


class ProgressWindow(object):
    """
    Query progress window
    """

    def __init__(self, mw):
        self.mw = mw
        self.app = QApplication.instance()
        self._win = None
        self._msg_count = defaultdict(int)
    # Creating progress dialogs
    ##########################################################################

    def update_labels(self, data):
        if self.abort():
            return

        if data.type == 'count':
            self._msg_count.update(data)
        else:
            return

        number_info = ''
        words_number, fields_number, fails_number = (
            self._msg_count['words_number'],
            self._msg_count['fields_number'],
            self._msg_count['fails_number']
        )
        if words_number or fields_number:
            number_info += _('QUERIED') + '<br>' + 45 * '-'
            number_info += u'<br>{0}: {1}{2}'.format(
                _('SUCCESS'), words_number, _('WORDS'))
            number_info += u'<br>{0}: {1}{2}'.format(
                _('UPDATE'), fields_number, _('FIELDS'))
            number_info += u'<br>{0}: {1}{2}'.format(
                _('FAILURE'), fails_number, _('WORDS'))

        self._update(label=number_info, value=words_number)
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
        self._win = QProgressDialog(label, '', min, max, parent)
        self._win.setWindowModality(Qt.ApplicationModal)
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
            self.app.processEvents(QEventLoop.ExcludeUserInputEvents)
            self._lastUpdate = time.time()

    def _setBusy(self):
        self._disabled = True
        self.mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))

    def _unsetBusy(self):
        self._disabled = False
        self.app.restoreOverrideCursor()
