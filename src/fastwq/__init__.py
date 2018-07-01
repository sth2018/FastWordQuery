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

import anki
import aqt
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap
from aqt.addcards import AddCards
from aqt.utils import showInfo, shortcut
from .ui import show_options
from .query import *
from .context import config, APP_ICON


have_setup = False
my_shortcut = ''


def query_decor(func, obj):
    def callback():
        return func(obj)
    return callback

def add_query_button(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_decor(
        query_from_editor_all_fields, self.editor))
    self.queryButton.setShortcut(QKeySequence(my_shortcut))
    self.queryButton.setToolTip(
        shortcut(_(u"Query (shortcut: %s)" % my_shortcut)))


def browser_menu():
    """
    添加插件菜单至浏览窗口菜单栏
    """
    def on_setup_menus(browser):
        """
        浏览窗口菜单钩子
        """
        # main menu
        menu = QMenu("Fast Word Query", browser.form.menubar)
        browser.form.menubar.addMenu(menu)
        # Query Selected
        action = QAction("Query Selected", browser)
        action.triggered.connect(query_decor(query_from_browser, (browser)))
        action.setShortcut(QKeySequence(my_shortcut))
        menu.addAction(action)
        #Options
        action = QAction("Options", browser)
        action.triggered.connect(show_options)
        menu.addAction(action)

    anki.hooks.addHook('browser.setupMenus', on_setup_menus)


def customize_addcards():
    """
    定制添加卡片界面
    """
    AddCards.setupButtons = wrap(
        AddCards.setupButtons, add_query_button, "before")


def config_menu():
    """
    添加菜单项至工具下拉菜单中
    """
    action = QAction(APP_ICON, "Fast Word Query...", mw)
    action.triggered.connect(show_options)
    mw.form.menuTools.addAction(action)
    global have_setup
    have_setup = True


def window_shortcut(key_sequence):
    """
    设置快捷键
    """
    global my_shortcut
    my_shortcut = key_sequence

