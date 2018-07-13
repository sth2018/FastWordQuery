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

from collections import defaultdict
import os
import shutil
import unicodedata

from aqt import mw
from aqt.qt import QFileDialog, QObject, QThread, pyqtSignal, pyqtSlot, QMutex
from aqt.utils import showInfo, showText, tooltip

from .constants import Endpoint, Template
from .context import config
from .lang import _, _sl
from .progress import ProgressWindow
from .service import service_manager, service_pool, QueryResult, copy_static_file
from .service.base import LocalService
from .utils import Empty, MapDict, Queue, wrap_css


__all__ = ['QueryThread', 'QueryWorkerManager', 'InvalidWordException',
    'query_from_browser', 'query_from_editor_all_fields',
    'query_all', 'update_note_fields', 'update_note_field',
    'promot_choose_css', 'add_to_tmpl', 'strip_combining', 
    'query_all_flds', 'inspect_note'
]


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

    note_flush = pyqtSignal(object)
    
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
                results, success_num, missed_css = query_all_flds(note)
                if not self.exit and self.manager:
                    if self.manager.update(note, results, success_num, missed_css):
                        self.note_flush.emit(note)
            except InvalidWordException:
                # only show error info on single query
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

    def get_worker(self):
        worker = QueryThread(self)
        worker.index = len(self.workers) + 1
        self.workers.append(worker)
        return worker

    def start(self):
        self.total = self.queue.qsize()
        self.progress.start(self.total, min=0)
        if self.total > 1:
            for x in range(0, min(config.thread_number, self.total)):
                self.get_worker()
                
            for worker in self.workers:
                worker.start()
        else:
            worker = self.get_worker()
            worker.run()
        
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
        
    def join(self):
        for worker in self.workers:
            while not worker.finished:
                if self.progress.abort():
                    worker.exit = True
                    break
                else:
                    self.progress.update_labels(MapDict(
                                type='count',
                                words_number = self.counter,
                                skips_number = self.skips,
                                fails_number = self.fails,
                                fields_number = self.fields))
                mw.app.processEvents()
                worker.wait(100)
        self.progress.finish()
    
    @pyqtSlot(object)
    def handle_flush(self, note):
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
        maps = config.get_maps(browser.editor.note.model()['id'])
        nomaps = True
        for each in maps:
            dict_unique = each.get('dict_unique', '').strip()
            if dict_unique:
                nomaps = False
                break
        if nomaps:
            from .ui import show_options
            show_options(browser)
        else:
            query_from_editor_all_fields(browser.editor)
    else:
        query_all(notes)
        # browser.model.reset()
 

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
    
    work_manager = QueryWorkerManager()
    #work_manager.reset()
    #progress.start(max=len(notes), min=0, immediate=True)
    queue = work_manager.queue
    
    for i, note in enumerate(notes):
        queue.put(note)
    
    work_manager.start()
    work_manager.join()
    
    #progress.finish()
    promot_choose_css(work_manager.missed_css)
    tooltip(u'{0} {1} {2}, {3} {4}'.format(_('UPDATED'), work_manager.counter, _('CARDS'), work_manager.fields, _('FIELDS')))
    #work_manager.clean()
    service_pool.clean()
    

def update_note_fields(note, results):
    """
    Update query result to note fields, return updated fields count.
    """

    if not results or not note or len(results) == 0:
        return 0
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

def promot_choose_css(missed_css):
    '''
    Choose missed css file and copy to user folder
    '''
    checked = set()
    for css in missed_css:
            filename = u'_' + css['file']
            if not os.path.exists(filename) and not css['file'] in checked:
                checked.add(css['file'])
                showInfo(
                    Template.miss_css.format(
                        dict = css['title'],
                        css = css['file']
                    )
                )
                try:
                    filepath = css['dict_path'][:css['dict_path'].rindex(os.path.sep)+1]
                    filepath = QFileDialog.getOpenFileName(
                        directory = filepath,
                        caption = u'Choose css file',
                        filter = u'CSS (*.css)'
                    )
                    if filepath:
                        shutil.copy(filepath, filename)
                        wrap_css(filename)

                except KeyError:
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

def strip_combining(txt):
    "Return txt with all combining characters removed."
    norm = unicodedata.normalize('NFKD', txt)
    return u"".join([c for c in norm if not unicodedata.combining(c)])

def query_all_flds(note):
    """
    Query all fields of single note
    """

    word_ord, word, maps = inspect_note(note)
    if not word:
        raise InvalidWordException
    
    if config.ignore_accents:
        word = strip_combining(unicode(word))
        
    # progress.update_title(u'Querying [[ %s ]]' % word)

    services = {}
    tasks = []
    for i, each in enumerate(maps):
        if i == word_ord:
            continue
        if i == len(note.fields):
            break
        #ignore field
        ignore = each.get('ignore', False)
        if ignore:
            continue
        #skip valued
        skip = each.get('skip_valued', False)
        if skip and len(note.fields[i]) != 0:
            continue
        #normal
        dict_unique = each.get('dict_unique', '').strip()
        dict_fld_ord = each.get('dict_fld_ord', -1)
        fld_ord = each.get('fld_ord', -1)
        if dict_unique and dict_fld_ord != -1 and fld_ord != -1:
            s = services.get(dict_unique, None)
            if s is None:
                s = service_pool.get(dict_unique)
                if s.support:
                    services[dict_unique] = s
            if s and s.support:
                tasks.append({'k': dict_unique, 'w': word, 'f': dict_fld_ord, 'i': fld_ord})
    
    success_num = 0
    result = defaultdict(QueryResult)
    for task in tasks:
        #try:
        service = services.get(task['k'], None)
        qr = service.active(task['f'], task['w'])
        if qr:
            result.update({task['i']: qr})
            success_num += 1
        #except:
        #    showInfo(_("NO_QUERY_WORD"))
        #    pass
    
    missed_css = list()
    for service in services.values():
        if isinstance(service, LocalService):
            for css in service.missed_css:
                missed_css.append({
                    'dict_path': service.dict_path,
                    'title': service.title,
                    'file': css
                })
        service_pool.put(service)
    
    return result, -1 if len(tasks) == 0 else success_num, missed_css
