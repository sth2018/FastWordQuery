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

import types
from PyQt4 import QtGui
from aqt import mw
from aqt.utils import showInfo
from .options import OptionsDialog
from .foldermanager import FoldersManageDialog
from ..libs import ankihub
from ..context import config
from ..lang import _
from ..constants import Endpoint, Template
from ..service import service_manager


__all__ = ['show_options', 'check_updates', 'show_fm_dialog', 'show_about_dialog']


def check_updates():
    '''check add-on last version'''
    try:
        if not ankihub.update([Endpoint.check_version], False, Endpoint.version):
            showInfo(_('LATEST_VERSION'))
    except:
        showInfo(_('CHECK_FAILURE'))


def show_fm_dialog(browser = None):
    '''open dictionary folder manager window'''
    parent = mw if browser is None else browser
    fm_dialog = FoldersManageDialog(parent, u'Dictionary Folder Manager')
    fm_dialog.activateWindow()
    fm_dialog.raise_()
    if fm_dialog.exec_() == QtGui.QDialog.Accepted:
        # update local services
        service_manager.update_services()
    # reshow options window
    show_options(browser)


def show_options(browser = None, model_id = -1, callback = None, *args, **kwargs):
    '''open options window'''
    parent = mw if browser is None else browser
    config.read()
    opt_dialog = OptionsDialog(parent, u'Options', model_id)
    opt_dialog.activateWindow()
    opt_dialog.raise_()
    if opt_dialog.exec_() == QtGui.QDialog.Accepted:
        if isinstance(callback, types.FunctionType):
            callback(*args, **kwargs)


def show_about_dialog(parent):
    '''open about dialog'''
    QtGui.QMessageBox.about(parent, _('ABOUT'), Template.tmpl_about)
