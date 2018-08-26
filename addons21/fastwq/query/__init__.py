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

from collections import defaultdict
import os
import shutil
import unicodedata

from aqt import mw
from aqt.utils import showInfo, showText, tooltip

from .worker import QueryWorkerManager
from .common import promot_choose_css, inspect_note

from ..constants import Endpoint, Template
from ..context import config
from ..lang import _
from ..gui import ProgressWindow
from ..service import service_manager, service_pool, QueryResult, copy_static_file
from ..service.base import LocalService
from ..utils import Empty, MapDict, Queue, wrap_css


__all__ = ['query_from_browser', 'query_from_editor_fields']


def query_from_browser(browser):
    """
    Query word from Browser
    """

    if not browser:
        return

    notes = [browser.mw.col.getNote(note_id)
             for note_id in browser.selectedNotes()]

    if len(notes) == 1:
        query_from_editor_fields(browser.editor)
    else:
        query_all(notes)
        # browser.model.reset()


def query_from_editor_fields(editor, fields=None):
    """
    Query word fileds from Editor
    """

    if not editor or not editor.note:
        return

    word_ord, word, maps = inspect_note(editor.note)
    flush = not editor.addMode
    nomaps = True
    for each in maps:
        dict_unique = each.get('dict_unique', '').strip()
        ignore = each.get('ignore', True)
        if dict_unique and not ignore:
            nomaps = False
            break
    if nomaps:
        from ..gui import show_options
        tooltip(_('PLS_SET_DICTIONARY_FIELDS'))
        show_options(
            editor.parentWindow,
            editor.note.model()['id'],
            query_from_editor_fields,
            editor,
            fields
        )
    else:
        editor.setNote(editor.note)
        query_all([editor.note], flush, fields)
        editor.setNote(editor.note, focusTo=0)
        editor.saveNow(lambda:None)


def query_all(notes, flush=True, fields=None):
    """
    Query maps word fileds
    """

    if len(notes) == 0:
        return

    work_manager = QueryWorkerManager()
    #work_manager.reset()
    #progress.start(max=len(notes), min=0, immediate=True)
    work_manager.flush = flush
    work_manager.query_fields = fields
    queue = work_manager.queue

    for note in notes:
        queue.put(note)

    work_manager.start()
    work_manager.join()

    #progress.finish()
    promot_choose_css(work_manager.missed_css)
    tooltip(u'{0} {1} {2}, {3} {4}'.format(_('UPDATED'), work_manager.counter, _(
        'CARDS'), work_manager.fields, _('FIELDS')))
    #work_manager.clean()
    service_pool.clean()
