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

from operator import itemgetter
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap
from aqt.addcards import AddCards
from aqt.utils import showInfo, shortcut, downArrow
from .gui import show_options, show_about_dialog, check_updates
from .query import query_from_browser, query_from_editor_fields
from .context import config, APP_ICON, Config
from .lang import _
from .service import service_pool
from .utils import get_icon


__all__ = [
    'browser_menu', 'customize_addcards', 
    'config_menu', 'check_updates', 'context_menu'
]


have_setup = False
my_shortcut = ''

_wraps = []
_OK_ICON = get_icon('ok.png')
_NULL_ICON = get_icon('null.png')


def browser_menu():
    """
    add add-on's menu to browser window
    """
    def on_setup_menus(browser):
        """
        on browser setupMenus was called
        """
        # 
        # main menu
        menu = QMenu("FastWQ", browser.form.menubar)
        browser.form.menubar.addMenu(menu)

        def set_options_def(mid, i):
            conf = config.get_maps(mid)
            conf = {'list': [conf], 'def': 0} if isinstance(conf, list) else conf
            if conf['def'] != i:
                conf['def'] = i
                data = dict()
                data[mid] = conf
                config.update(data)
        # end set_options_def

        def init_fastwq_menu(*args, **kwargs):
            menu.clear()
            # Query Selected
            action = QAction(_('QUERY_SELECTED'), browser)
            action.triggered.connect(lambda: query_from_browser(browser))
            action.setShortcut(QKeySequence(my_shortcut))
            menu.addAction(action)
            # Options
            action = QAction(_('OPTIONS'), browser)
            def _show_options():
                model_id = -1
                for note_id in browser.selectedNotes():
                    note = browser.mw.col.getNote(note_id)
                    model_id = note.model()['id']
                    break
                show_options(browser, model_id)
            action.triggered.connect(_show_options)
            menu.addAction(action)

            # Default configs
            menu.addSeparator()
            b = False
            for m in sorted(browser.mw.col.models.all(), key=itemgetter("name")):
                conf = config.get_maps(m['id'])
                conf = {'list': [conf], 'def': 0} if isinstance(conf, list) else conf
                maps_list = conf['list']
                if len(maps_list) > 1:
                    submenu = menu.addMenu(m['name'])
                    for i, maps in enumerate(maps_list):
                        submenu.addAction(
                            _OK_ICON if i==conf['def'] else _NULL_ICON,
                            _('CONFIG_INDEX') % (i+1) if isinstance(maps, list) else maps['name'],
                            lambda mid=m['id'], i=i: set_options_def(mid, i)
                        )
                    b = True
            if b: 
                menu.addSeparator()

            # About
            action = QAction(_('ABOUT'), browser)
            action.triggered.connect(lambda: show_about_dialog(browser))
            menu.addAction(action)

        # end init_fastwq_menu
        init_fastwq_menu()
        # wrap config.update
        if Config.update not in _wraps:
            Config.update = wrap(
                Config.update,
                init_fastwq_menu,
                "after"
            )
            _wraps.append(Config.update)
    addHook('browser.setupMenus', on_setup_menus)


def customize_addcards():
    """
    add button to addcards window
    """
    def add_query_button(self):
        '''
        add a button in add card window
        '''
        bb = self.form.buttonBox
        ar = QDialogButtonBox.ActionRole
        # button
        fastwqBtn = QPushButton(_("QUERY") + u" " + downArrow())
        fastwqBtn.setShortcut(QKeySequence(my_shortcut))
        fastwqBtn.setToolTip(
            _(u"Shortcut: %s") % shortcut(my_shortcut)
        )
        bb.addButton(fastwqBtn, ar)
        # signal
        def onQuery(e):
            if isinstance(e, QMouseEvent):
                if e.buttons() & Qt.LeftButton:
                    menu = QMenu(self)
                    menu.addAction(_("QUERY"), lambda: query_from_editor_fields(self.editor), QKeySequence(my_shortcut))
                    menu.addAction(_("OPTIONS"), lambda: show_options(self, self.editor.note.model()['id']))
                    menu.exec_(fastwqBtn.mapToGlobal(QPoint(0, fastwqBtn.height())))
            else:
                query_from_editor_fields(self.editor)

        fastwqBtn.mousePressEvent = onQuery
        fastwqBtn.clicked.connect(onQuery)
    
    AddCards.setupButtons = wrap(
        AddCards.setupButtons, 
        add_query_button, 
        "after"
    )


def config_menu():
    """
    add menu to anki window menebar
    """
    action = QAction(APP_ICON, "FastWQ...", mw)
    action.triggered.connect(lambda: show_options())
    mw.form.menuTools.addAction(action)


def context_menu():
    '''mouse right click menu'''
    def on_setup_menus(web_view, menu):
        """
        add context menu to webview
        """
        current_model_id = web_view.editor.note.model()['id']
        conf = config.get_maps(current_model_id)
        maps_list = conf if isinstance(conf, list) else conf['list']
        curr_flds = []
        names = []
        for i, maps in enumerate(maps_list):
            maps = maps if isinstance(maps, list) else maps['fields']
            for mord, m in enumerate(maps):
                if m.get('word_checked', False):
                    word_ord = mord
                    break
            if web_view.editor.currentField != word_ord:
                each = maps[web_view.editor.currentField]
                ignore = each.get('ignore', False)
                if not ignore:
                    dict_unique = each.get('dict_unique', '').strip()
                    dict_fld_ord = each.get('dict_fld_ord', -1)
                    fld_ord = each.get('fld_ord', -1)
                    if dict_unique and dict_fld_ord != -1 and fld_ord != -1:
                        s = service_pool.get(dict_unique)
                        if s and s.support:
                            name = s.title + ' :-> ' + s.fields[dict_fld_ord]
                            if name not in names:
                                names.append(name)
                                curr_flds.append({
                                    'name': name,
                                    'def': i
                                })
                        service_pool.put(s)

        submenu = menu.addMenu(_('QUERY'))
        submenu.addAction(_('ALL_FIELDS'), lambda: query_from_editor_fields(web_view.editor), QKeySequence(my_shortcut))
        if len(curr_flds) > 0:
            # quer hook method
            def query_from_editor_hook(i):
                conf = config.get_maps(current_model_id)
                maps_list = {'list': [conf], 'def': i} if isinstance(conf, list) else conf
                maps_list['def'] = i
                data = dict()
                data[current_model_id] = maps_list
                config.update(data)
                query_from_editor_fields(
                    web_view.editor,
                    fields=[web_view.editor.currentField]
                )
            # sub menu
            #flds_menu = submenu.addMenu(_('CURRENT_FIELDS'))
            submenu.addSeparator()
            for c in curr_flds:
                submenu.addAction(c['name'], 
                    lambda i=c['def']: query_from_editor_hook(i)
                )
            submenu.addSeparator()
        submenu.addAction(_("OPTIONS"), lambda: show_options(web_view, web_view.editor.note.model()['id']))

    addHook('EditorWebView.contextMenuEvent', on_setup_menus)
