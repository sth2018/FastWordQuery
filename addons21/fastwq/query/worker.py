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


from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from anki.notes import Note

from ..context import config
from ..lang import _
from ..gui import ProgressWindow
from ..utils import Empty, MapDict, Queue

from .common import InvalidWordException, query_flds, update_note_fields


__all__ = ['QueryWorkerManager']


class QueryThread(QThread):
    """
    Query Worker Thread
    """

    note_flush = pyqtSignal(Note)

    def __init__(self, manager):
        super(QueryThread, self).__init__()
        self.index = 0
        self.exit = False
        self.finished = False
        self.manager = manager
        self.note_flush.connect(manager.handle_flush)

    def run(self):
        while True:
            if self.exit or not self.manager:
                break
            try:
                note = self.manager.queue.get(True, timeout=0.1)
            except Empty:
                self.exit = True
                continue

            try:
                results, success_num, missed_css = query_flds(note, self.manager.query_fields)
                if not self.exit and self.manager:
                    if self.manager.update(note, results, success_num, missed_css):
                        self.note_flush.emit(note)
            except InvalidWordException:
                # only show error info on single query
                self.manager.fails += 1
                if self.manager.total == 1:
                    showInfo(_("NO_QUERY_WORD"))

            if self.manager:
                self.manager.queue.task_done()

        self.finished = True


class QueryWorkerManager(object):
    """
    Query Worker Thread Manager
    """

    def __init__(self):
        self.workers = []
        self.queue = Queue()
        self.mutex = QMutex()
        self.progress = ProgressWindow(mw)
        self.total = 0
        self.counter = 0
        self.fails = 0
        self.fields = 0
        self.skips = 0
        self.missed_css = list()
        self.flush = True
        self.query_fields = None

    def get_worker(self):
        worker = QueryThread(self)
        worker.index = len(self.workers) + 1
        self.workers.append(worker)
        return worker

    def start(self):
        self.total = self.queue.qsize()
        self.progress.start(max=self.total, min=0)
        self.update_progress()
        if self.total > 1:
            for _ in range(0, min(config.thread_number, self.total)):
                self.get_worker()

            for worker in self.workers:
                worker.start()
        else:
            worker = self.get_worker()
            worker.run()
            self.update_progress()

    def update(self, note, results, success_num, missed_css):
        self.mutex.lock()
        if success_num > 0:
            self.counter += 1
        elif success_num == 0:
            self.fails += 1
        else:
            self.skips += 1
        val = update_note_fields(note, results)
        self.fields += val
        self.missed_css += missed_css
        self.mutex.unlock()
        if self.total > 1:
            return val > 0
        else:
            self.handle_flush(note)
            return False

    def update_progress(self):
        self.progress.update_labels(MapDict(
            type='count',
            words_number=self.counter,
            skips_number=self.skips,
            fails_number=self.fails,
            fields_number=self.fields
        ))
        mw.app.processEvents()

    def join(self):
        for worker in self.workers:
            while not worker.finished:
                if self.progress.abort():
                    worker.exit = True
                    break
                else:
                    self.update_progress()
                mw.app.processEvents()
                worker.wait(30)
        self.progress.finish()
    
    def handle_flush(self, note):
        if self.flush and note:
            note.flush()
