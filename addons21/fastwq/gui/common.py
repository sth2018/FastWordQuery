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

import types

from aqt import mw
from aqt.qt import *

from ..constants import Template
from ..context import config
from ..lang import _
from ..service import service_manager, service_pool
from .dictmanager import DictManageDialog
from .foldermanager import FoldersManageDialog
from .options import OptionsDialog

__all__ = ['show_options', 'show_fm_dialog', 'show_about_dialog']


def show_fm_dialog(browser=None):
    '''open dictionary folder manager window'''
    parent = mw if browser is None else browser
    fm_dialog = FoldersManageDialog(parent, u'Dictionary Folder Manager')
    fm_dialog.activateWindow()
    fm_dialog.raise_()
    if fm_dialog.exec_() == QDialog.Accepted:
        # update local services
        service_pool.clean()
        service_manager.update_services()
    fm_dialog.destroy()
    # reshow options window
    show_options(browser)


def show_dm_dialog(browser=None):
    parent = mw if browser is None else browser
    dm_dialog = DictManageDialog(parent, u'Dictionary Manager')
    dm_dialog.activateWindow()
    dm_dialog.raise_()
    if dm_dialog.exec_() == QDialog.Accepted:
        # update local services
        service_pool.clean()
        service_manager.update_services()
    dm_dialog.destroy()
    # reshow options window
    show_options(browser)


def show_options(browser=None, model_id=-1, callback=None, *args, **kwargs):
    '''open options window'''
    parent = mw if browser is None else browser
    config.read()
    opt_dialog = OptionsDialog(parent, u'Options', model_id)
    opt_dialog.activateWindow()
    opt_dialog.raise_()
    result = opt_dialog.exec_()
    opt_dialog.destroy()
    if result == QDialog.Accepted:
        if isinstance(callback, types.FunctionType):
            callback(*args, **kwargs)
    elif result == 1001:
        show_fm_dialog(parent)
    elif result == 1002:
        show_dm_dialog(parent)


def show_about_dialog(parent):
    '''open about dialog'''
    QMessageBox.about(parent, _('ABOUT'), Template.tmpl_about)
