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

from collections import defaultdict
import os
import re
import shutil
import sys
import time

from aqt import mw
from aqt.qt import QFileDialog, QObject, QThread, pyqtSignal, pyqtSlot, QMutex
from aqt.utils import showInfo, showText, tooltip

from .constants import Endpoint, Template
from .context import config
from .lang import _, _sl
from .progress import ProgressManager
from .service import service_manager, QueryResult, copy_static_file
from .utils import Empty, MapDict, Queue, wrap_css



def inspect_note(note):
    """
    inspect the note, and get necessary input parameters
    return word_ord: field index of the word in current note
    return word: the word
    return maps: dicts map of current note
    """

    maps = config.get_maps(note.model()['id'])
    for i, m in enumerate(maps):
        if m.get('word_checked', False):
            word_ord = i
            break
    else:
        # if no field is checked to be the word field, default the
        # first one.
        word_ord = 0

    def purify_word(word):
        return word.strip() if word else ''

    word = purify_word(note.fields[word_ord])
    return word_ord, word, maps


class QueryThread(QThread):
    """
    Query Worker Thread
    """
    
    progress_update = pyqtSignal(dict)
    note_flush = pyqtSignal(object)
    
    def __init__(self, manager):
        super(QueryThread, self).__init__()
        self.index = 0
        self.exit = False
        self.manager = manager
        self.progress_update.connect(progress.update_labels)
        self.note_flush.connect(handle_flush)

    def run(self):
        while True:
            if progress.abort() or self.exit or self.manager == None:
                break
            try:
                note = self.manager.queue.get(True, timeout=0.1)
            except Empty:
                self.exit = True
                continue
                
            try:
                results, success_num = query_all_flds(note)
                if self.manager:
                    if self.manager.update(note, results, success_num):
                        self.note_flush.emit(note)
                    # Update progress window infomation
                    self.progress_update.emit(
                        MapDict(
                            type='count',
                            words_number = self.manager.counter,
                            fails_number = self.manager.fails,
                            fields_number = self.manager.fields)
                        )
                    
            except InvalidWordException:
                showInfo(_("NO_QUERY_WORD"))
                

class QueryWorkerManager(object):
    """
    Query Worker Thread Manager
    """
    
    def __init__(self):
        self.workers = []
        self.queue = Queue()
        self.mutex = QMutex()
        self.total = 0
        self.counter = 0
        self.fields = 0

    def get_worker(self):
        worker = QueryThread(self)
        worker.index = len(self.workers) + 1
        self.workers.append(worker)
        return worker

    def start(self):
        for x in range(0, min(config.thread_number, self.queue.qsize())):
            self.get_worker()
            
        self.total = self.queue.qsize()
        for worker in self.workers:
            worker.start()

    def reset(self):
        for worker in self.workers:
            worker.exit = True
            worker.manager = None
            worker.terminate()
        
        self.mutex.unlock()
        self.workers = []
        self.queue = Queue()
        self.total = 0
        self.counter = 0
        self.fails = 0
        self.fields = 0
    
    def clean(self):
        self.reset()
        
    def update(self, note, results, success_num):
        self.mutex.lock()
        if success_num > 0:
            self.counter += 1
        else:
            self.fails += 1
        val = update_note_fields(note, results)
        self.fields += val
        self.mutex.unlock()
        return val > 0
        
    def join(self):
        for worker in self.workers:
            while not worker.isFinished():
                if progress.abort():
                    break
                mw.app.processEvents()
                worker.wait(100)
        

@pyqtSlot(object)
def handle_flush(note):
    if note:
        note.flush()
    

def query_from_browser(browser):
    """
    Query word from Browser
    """

    if not browser:
        return
    
    notes = [browser.mw.col.getNote(note_id)
             for note_id in browser.selectedNotes()]
    
    if len(notes) == 1:
        query_from_editor_all_fields(browser.editor)
        return
    
    query_all(notes)
    browser.model.reset()
 

def query_from_editor_all_fields(editor):
    """
    Query word fileds from Editor
    """

    if not editor or not editor.note:
        return
    
    query_all([editor.note])
    editor.setNote(editor.note, focus=True)
    editor.saveNow()
    
   
def query_all(notes):
    """
    Query maps word fileds
    """

    if len(notes) == 0:
        return
    
    work_manager.reset()
    progress.start(max=len(notes), min=0, immediate=True)
    queue = work_manager.queue
    
    for i, note in enumerate(notes):
        queue.put(note)
    
    work_manager.start()
    work_manager.join()
    
    progress.finish()
    promot_choose_css()
    tooltip(u'{0} {1} {2}, {3} {4}'.format(_('UPDATED'), work_manager.counter, _('CARDS'), work_manager.fields, _('FIELDS')))
    work_manager.clean()
    service_pool.clean();
    

def update_note_fields(note, results):
    """
    Update query result to note fields, return updated fields count.
    """

    if not results or not note or len(results) == 0:
        return
    count = 0
    for i, q in results.items():
        if isinstance(q, QueryResult) and i < len(note.fields):
            count += update_note_field(note, i, q)
          
    return count
    

def update_note_field(note, fld_index, fld_result):
    """
    Update single field, if result is valid then return 1, else return 0
    """

    result, js, jsfile = fld_result.result, fld_result.js, fld_result.jsfile
    # js process: add to template of the note model
    add_to_tmpl(note, js=js, jsfile=jsfile)
    # if not result:
    #     return
    if not config.force_update and not result:
        return 0
    
    value = result if result else ''
    if note.fields[fld_index] != value:
        note.fields[fld_index] = value
        return 1
    
    return 0

def promot_choose_css():
    for local_service in service_manager.local_services:
        try:
            missed_css = local_service.missed_css.pop()
            showInfo(Template.miss_css.format(
                dict=local_service.title, css=missed_css))
            filepath = QFileDialog.getOpenFileName(
                caption=u'Choose css file', filter=u'CSS (*.css)')
            if filepath:
                shutil.copy(filepath, u'_' + missed_css)
                wrap_css(u'_' + missed_css)
                local_service.missed_css.clear()

        except KeyError as e:
            pass


def add_to_tmpl(note, **kwargs):
    # templates
    '''
    [{u'name': u'Card 1', u'qfmt': u'{{Front}}\n\n', u'did': None, u'bafmt': u'',
        u'afmt': u'{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n\n{{12}}\n\n{{44}}\n\n', u'ord': 0, u'bqfmt': u''}]
    '''
    # showInfo(str(kwargs))
    afmt = note.model()['tmpls'][0]['afmt']
    if kwargs:
        jsfile, js = kwargs.get('jsfile', None), kwargs.get('js', None)
        if js and js.strip():
            addings = js.strip()
            if addings not in afmt:
                if not addings.startswith(u'<script') and not addings.endswith(u'/script>'):
                    addings = u'\r\n<script>{}</script>'.format(addings)
                afmt += addings
        if jsfile:
            new_jsfile = u'_' + \
                jsfile if not jsfile.startswith(u'_') else jsfile
            copy_static_file(jsfile, new_jsfile)
            addings = u'\r\n<script src="{}"></script>'.format(new_jsfile)
            afmt += addings
        note.model()['tmpls'][0]['afmt'] = afmt


class InvalidWordException(Exception):
    """Invalid word exception"""

def query_all_flds(note):
    """
    Query all fields of single note
    """

    word_ord, word, maps = inspect_note(note)
    if not word:
        raise InvalidWordException
    
    progress.update_title(u'Querying [[ %s ]]' % word)

    services = {}
    tasks = []
    for i, each in enumerate(maps):
        if i == word_ord:
            continue
        if i == len(note.fields):
            break
        dict_name = each.get('dict', '').strip()
        dict_field = each.get('dict_field', '').strip()
        dict_unique = each.get('dict_unique', '').strip()
        if dict_name and dict_name not in _sl('NOT_DICT_FIELD') and dict_field:
            s = services.get(dict_unique, None)
            if s == None:
                services[dict_unique] = service_pool.get(dict_unique)#service_manager.get_service(dict_unique)
            tasks.append({'k': dict_unique, 'w': word, 'f': dict_field, 'i': i})
    
    success_num = 0
    result = defaultdict(QueryResult)
    for task in tasks:
        try:
            service = services.get(task['k'], None)
            qr = service.active(task['f'], task['w'])
            if qr:
                result.update({task['i']: qr})
                success_num += 1
        except:
            showInfo(_("NO_QUERY_WORD"))
            pass
        
    for service in services.values():
        service_pool.put(service)
    
    return result, success_num


class ServicePool(object):
    """
    Service instance pool
    """
    def __init__(self):
        self.pools = {}
        
    def get(self, unique):
        queue = self.pools.get(unique, None)
        if queue:
            try:
                return queue.get(True, timeout=0.1)
            except Empty:
                pass
        
        return service_manager.get_service(unique)
    
    def put(self, service):
        unique = service.unique
        queue = self.pools.get(unique, None)
        if queue == None:
            queue = Queue()
            self.pools[unique] = queue
            
        queue.put(service)
        
    def clean(self):
        self.pools = {}
        

progress = ProgressManager(mw)                  # progress window
work_manager = QueryWorkerManager()             # Query Worker Thread Manager
service_pool = ServicePool()                    # Service Instance Pool Manager
