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

import sys

import anki
import aqt
import aqt.models
import sip
from anki.utils import isMac
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck

from ..constants import Endpoint
from ..context import config
from ..lang import _, _sl
from ..service import service_manager, service_pool
from ..utils import get_icon, get_model_byId
from .base import WIDGET_SIZE, Dialog
from .setting import SettingDialog

__all__ = ['OptionsDialog']


class OptionsDialog(Dialog):
    '''
    query options window
    setting query dictionary and fileds
    '''

    __slot__ = ['before_build', 'after_build']
    _signal = pyqtSignal(str)

    _NULL_ICON = get_icon('null.png')
    _OK_ICON = get_icon('ok.png')

    def __init__(self, parent, title=u'Options', model_id=-1):
        super(OptionsDialog, self).__init__(parent, title)
        self._signal.connect(self._before_build)
        self._signal.connect(self._after_build)
        # initlizing info
        self.main_layout = QVBoxLayout()
        self.loading_label = QLabel(_('INITLIZING_DICT'))
        self.main_layout.addWidget(self.loading_label, 0, Qt.AlignCenter)
        # self.loading_layout.addLayout(models_layout)
        self.setLayout(self.main_layout)
        # initlize properties
        self.model_id = model_id if model_id != -1 else config.last_model_id
        self.current_model = None
        self.tabs = []
        self.dict_services = None
        # size and signal
        self.resize(
            WIDGET_SIZE.dialog_width,
            4 * WIDGET_SIZE.map_max_height + WIDGET_SIZE.dialog_height_margin)
        self._signal.emit('before_build')

    def _before_build(self, s):
        if s != 'before_build':
            return
        # dict service list
        dicts = config.dicts
        self.dict_services = {
            'local': [],  # 本地词典
            'web': []  # 网络词典
        }
        for clazz in service_manager.local_services:
            if dicts.get(clazz.__unique__, dict()).get('enabled', True):
                service = service_pool.get(clazz.__unique__)
                if service and service.support:
                    self.dict_services['local'].append({
                        'title': service.title,
                        'unique': service.unique
                    })
                service_pool.put(service)
        for clazz in service_manager.web_services:
            if dicts.get(clazz.__unique__, dict()).get('enabled', True):
                service = service_pool.get(clazz.__unique__)
                if service and service.support:
                    self.dict_services['web'].append({
                        'title': service.title,
                        'unique': service.unique
                    })
                service_pool.put(service)
        # emit finished
        self._signal.emit('after_build')

    def _after_build(self, s):
        if s != 'after_build':
            return
        if self.loading_label:
            self.main_layout.removeWidget(self.loading_label)
            sip.delete(self.loading_label)
            self.loading_label = None
        models_layout = QHBoxLayout()
        # add buttons
        mdx_button = QPushButton(_('DICTS_FOLDERS'))
        mdx_button.clicked.connect(self.show_fm_dialog)
        self.models_button = QPushButton(_('CHOOSE_NOTE_TYPES'))
        self.models_button.clicked.connect(self.btn_models_pressed)
        models_layout.addWidget(mdx_button)
        models_layout.addWidget(self.models_button)
        self.main_layout.addLayout(models_layout)
        # tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBar(CTabBar())
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { /* The tab widget frame */
                border: 1px solid #c3c3c3;
            }
            """)
        tab_corner = QWidget()
        tab_corner_layout = QHBoxLayout()
        tab_corner_layout.setSpacing(1)
        tab_corner_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        tab_corner_layout.setContentsMargins(0, 0, 0, 0)
        tab_corner.setLayout(tab_corner_layout)
        tab_add_button = QToolButton(self)
        tab_add_button.setIcon(get_icon('add.png'))
        tab_set_button = QToolButton(self)
        if isMac and sys.hexversion < 0x03000000:
            tab_set_button.setMaximumSize(20, 20)
            tab_add_button.setMaximumSize(20, 20)
        tab_set_button.setIcon(get_icon('setting.png'))
        tab_corner_layout.addWidget(tab_set_button)
        tab_corner_layout.addWidget(tab_add_button)
        self.tab_widget.setCornerWidget(tab_corner)
        # signals
        tab_set_button.clicked.connect(self.show_dm_dialog)
        tab_add_button.clicked.connect(self.addTab)
        self.tab_widget.tabCloseRequested.connect(self.removeTab)
        # layout
        self.main_layout.addWidget(self.tab_widget)
        # add description of radio buttons AND ok button
        bottom_layout = QHBoxLayout()
        paras_btn = QPushButton(_('SETTINGS'))
        paras_btn.clicked.connect(self.show_paras)
        about_btn = QPushButton(_('ABOUT'))
        about_btn.clicked.connect(self.show_about)
        # about_btn.clicked.connect(self.show_paras)
        # chk_update_btn = QPushButton(_('UPDATE'))
        # chk_update_btn.clicked.connect(self.check_updates)
        home_label = QLabel(
            '<a href="{url}">User Guide</a>'.format(url=Endpoint.user_guide))
        home_label.setOpenExternalLinks(True)
        # buttons
        btnbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        btnbox.accepted.connect(self.accept)
        bottom_layout.addWidget(paras_btn)
        # bottom_layout.addWidget(chk_update_btn)
        bottom_layout.addWidget(about_btn)
        bottom_layout.addWidget(home_label)
        bottom_layout.addWidget(btnbox)
        # self.setLayout(self.main_layout)
        self.main_layout.addLayout(bottom_layout)
        # init from saved data
        self.current_model = None
        if self.model_id:
            self.current_model = get_model_byId(mw.col.models, self.model_id)
        if self.current_model:
            self.models_button.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'),
                              self.current_model['name']))
            # build fields -- dicts layout
            self.build_tabs_layout()

    def show_paras(self):
        '''open setting dialog'''
        dialog = SettingDialog(self, u'Setting')
        dialog.exec_()
        dialog.destroy()

    # def check_updates(self):
    #     '''check addon version'''
    #     from .common import check_updates
    #     check_updates(parent=self)

    def show_fm_dialog(self):
        '''open folder manager dialog'''
        self.accept()
        self.setResult(1001)

    def show_dm_dialog(self):
        '''open dictionary manager dialog'''
        self.accept()
        self.setResult(1002)

    def show_about(self):
        '''open about dialog'''
        from .common import show_about_dialog
        show_about_dialog(self)

    def accept(self):
        '''on button was clicked'''
        self.save()
        super(OptionsDialog, self).accept()

    def btn_models_pressed(self):
        '''on choose model button was clicker'''
        self.save()
        self.current_model = self.show_models()
        if self.current_model:
            self.build_tabs_layout()

    def build_tabs_layout(self):
        '''
        build dictionary、fields etc
        '''
        try:
            self.tab_widget.currentChanged.disconnect()
        except Exception:
            pass
        while len(self.tabs) > 0:
            self.removeTab(0, True)
        # tabs
        conf = config.get_maps(self.current_model['id'])
        maps_list = {
            'list': [conf],
            'def': 0
        } if isinstance(conf, list) else conf
        for maps in maps_list['list']:
            self.addTab(maps, False)
        self.tab_widget.currentChanged.connect(self.changedTab)
        # value
        self.changedTab(maps_list['def'])
        self.tab_widget.setCurrentIndex(maps_list['def'])
        # size
        self.resize(
            WIDGET_SIZE.dialog_width,
            min(max(3,
                    len(self.current_model['flds']) + 1), 14) *
            WIDGET_SIZE.map_max_height + WIDGET_SIZE.dialog_height_margin)
        self.save()

    def addTab(self, maps=None, forcus=True):
        i = len(self.tabs)
        if isinstance(maps, list):
            maps = {'fields': maps, 'name': _('CONFIG_INDEX') % (i + 1)}
        tab = TabContent(self.current_model, maps['fields'] if maps else None,
                         self.dict_services)
        self.tabs.append(tab)
        self.tab_widget.addTab(
            tab, maps['name'] if maps else _('CONFIG_INDEX') % (i + 1))
        if forcus:
            self.tab_widget.setCurrentIndex(i)

    def removeTab(self, i, forcus=False):
        # less than one config
        if not forcus and len(self.tabs) <= 1:
            return
        tab = self.tabs[i]
        del self.tabs[i]
        self.tab_widget.removeTab(i)
        tab.destroy()
        # for k in range(0, len(self.tabs)):
        #    self.tab_widget.setTabText(k, _('CONFIG_INDEX') % (k+1))

    def changedTab(self, i):
        if not isMac or sys.hexversion >= 0x03000000:
            # restore
            for k in range(0, len(self.tabs)):
                self.tab_widget.setTabIcon(k, self._NULL_ICON)
            # add flag
            self.tab_widget.setTabIcon(i, self._OK_ICON)
        self.tabs[i].build_layout()

    def show_models(self):
        '''
        show choose note type window
        '''
        edit = QPushButton(
            anki.lang._("Manage"), clicked=lambda: aqt.models.Models(mw, self))
        ret = StudyDeck(
            mw,
            names=lambda: sorted(mw.col.models.allNames()),
            accept=anki.lang._("Choose"),
            title=anki.lang._("Choose Note Type"),
            help="_notes",
            parent=self,
            buttons=[edit],
            cancel=True,
            geomKey="selectModel")
        if ret.name:
            model = mw.col.models.byName(ret.name)
            self.models_button.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'), ret.name))
            return model

    def save(self):
        '''save config to file'''
        if not self.current_model:
            return
        data = dict()
        maps_list = {'list': [], 'def': self.tab_widget.currentIndex()}
        for i, tab in enumerate(self.tabs):
            maps_list['list'].append({
                'fields':
                tab.data,
                'name':
                self.tab_widget.tabBar().tabText(i)
            })
        current_model_id = str(self.current_model['id'])
        data[current_model_id] = maps_list
        data['last_model'] = self.current_model['id']
        config.update(data)


class TabContent(QScrollArea):
    '''Options tab content'''

    def __init__(self, model, conf, services):
        super(TabContent, self).__init__()
        self._conf = conf
        self._model = model
        self._services = services
        self._last_checkeds = None
        self._options = list()
        self._was_built = False
        # dicts mapping
        dicts = QWidget(self)
        dicts.setLayout(QGridLayout())
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.setWidget(dicts)
        self.dicts_layout = dicts.layout()
        # self.dicts_layout.setSizeConstraint(QLayout.SetFixedSize)

    def build_layout(self):
        '''
        build dictionary、fields etc
        '''
        if self._was_built:
            return

        del self._options[:]
        self._last_checkeds = None
        self._was_built = True

        model = self._model
        maps = self._conf

        # labels
        f = QFont()
        f.setBold(True)
        labels = [u'＃', '', 'DICTS', 'DICT_FIELDS', '']
        for i, s in enumerate(labels):
            if s:
                label = QLabel(_(s))
                label.setFont(f)
                label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.dicts_layout.addWidget(label, 0, i)

        # ignore all
        self.ignore_all_check_btn = QCheckBox(_('SELECT_ALL'))
        self.ignore_all_check_btn.setFont(f)
        self.ignore_all_check_btn.setEnabled(True)
        self.ignore_all_check_btn.setChecked(True)
        self.dicts_layout.addWidget(self.ignore_all_check_btn, 0, 1)
        self.ignore_all_check_btn.clicked.connect(
            self.ignore_all_check_changed)

        # Skip valued all
        self.skip_all_check_btn = QCheckBox(_('SELECT_ALL'))
        self.skip_all_check_btn.setFont(f)
        self.skip_all_check_btn.setEnabled(True)
        self.skip_all_check_btn.setChecked(True)
        self.dicts_layout.addWidget(self.skip_all_check_btn, 0, 4)
        self.skip_all_check_btn.clicked.connect(self.skip_all_check_changed)

        # dict & fields
        self.radio_group = QButtonGroup()
        for i, fld in enumerate(model['flds']):
            ord = fld['ord']
            name = fld['name']
            if maps:
                for j, each in enumerate(maps):
                    if each.get('fld_ord', -1) == ord or each.get(
                            'fld_name', '') == name:
                        each['fld_name'] = name
                        each['fld_ord'] = ord
                        self.add_dict_layout(j, **each)
                        break
                else:
                    self.add_dict_layout(
                        i, fld_name=name, fld_ord=ord, word_checked=i == 0)
            else:
                self.add_dict_layout(
                    i, fld_name=name, fld_ord=ord, word_checked=i == 0)

        # update
        self.ignore_all_update()
        self.skip_all_update()

    def add_dict_layout(self, i, **kwargs):
        """
        add dictionary fields row
        """
        word_checked = kwargs.get('word_checked', False)

        fld_name, fld_ord = (
            kwargs.get('fld_name', ''),  # 笔记类型的字段名
            kwargs.get('fld_ord', ''),  # 笔记类型的字段编号
        )

        dict_name, dict_unique, dict_fld_name, dict_fld_ord = (
            kwargs.get('dict_name', ''),  # 字典名
            kwargs.get('dict_unique', ''),  # 字典ID
            kwargs.get('dict_fld_name', ''),  # 对应字典的字段名
            kwargs.get('dcit_fld_ord', 0)  # 对应字典的字段编号
        )

        ignore, skip, cloze = (
            kwargs.get('ignore', True),  # 忽略标志
            kwargs.get('skip_valued', True),  # 略过有值项标志
            kwargs.get('cloze_word', False),  # 单词填空
        )

        # check
        word_check_btn = QRadioButton(fld_name)
        word_check_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        word_check_btn.setCheckable(True)
        word_check_btn.setChecked(word_checked)
        self.radio_group.addButton(word_check_btn)
        # dict combox
        dict_combo = QComboBox()
        dict_combo.setMinimumSize(WIDGET_SIZE.map_dict_width, 0)
        dict_combo.setMaximumSize(WIDGET_SIZE.map_dict_width,
                                  WIDGET_SIZE.map_max_height)
        dict_combo.setFocusPolicy(Qt.TabFocus | Qt.ClickFocus | Qt.StrongFocus
                                  | Qt.WheelFocus)
        ignore = not self.fill_dict_combo_options(dict_combo, dict_unique,
                                                  self._services) or ignore
        dict_unique = dict_combo.itemData(dict_combo.currentIndex())
        dict_combo.setEnabled(not word_checked and not ignore)
        # field combox
        field_combo = QComboBox()
        field_combo.setMinimumSize(WIDGET_SIZE.map_field_width, 0)
        field_combo.setMaximumSize(WIDGET_SIZE.map_field_width,
                                   WIDGET_SIZE.map_max_height)
        field_combo.setEnabled(not word_checked and not ignore)
        self.fill_field_combo_options(field_combo, dict_name, dict_unique,
                                      dict_fld_name, dict_fld_ord)

        # ignore
        ignore_check_btn = QCheckBox(_("NOT_DICT_FIELD"))
        ignore_check_btn.setEnabled(not word_checked)
        ignore_check_btn.setChecked(ignore)

        # Skip valued
        skip_check_btn = QCheckBox(_("SKIP_VALUED"))
        skip_check_btn.setEnabled(not word_checked and not ignore)
        skip_check_btn.setChecked(skip)

        # Skip valued
        cloze_check_btn = QCheckBox(_("CLOZE_WORD"))
        cloze_check_btn.setEnabled(not word_checked and not ignore)
        cloze_check_btn.setChecked(cloze)

        # events
        # word
        def radio_btn_checked():
            if self._last_checkeds:
                self._last_checkeds[0].setEnabled(True)
                ignore = self._last_checkeds[0].isChecked()
                for i in range(1, len(self._last_checkeds)):
                    self._last_checkeds[i].setEnabled(not ignore)

            word_checked = word_check_btn.isChecked()
            ignore_check_btn.setEnabled(not word_checked)
            ignore = ignore_check_btn.isChecked()
            dict_combo.setEnabled(not word_checked and not ignore)
            field_combo.setEnabled(not word_checked and not ignore)
            skip_check_btn.setEnabled(not word_checked and not ignore)
            cloze_check_btn.setEnabled(not word_checked and not ignore)
            if word_checked:
                self._last_checkeds = [
                    ignore_check_btn, dict_combo, field_combo, skip_check_btn
                ]

        word_check_btn.clicked.connect(radio_btn_checked)
        if word_checked:
            self._last_checkeds = None
            radio_btn_checked()

        # ignor
        def ignore_check_changed():
            word_checked = word_check_btn.isChecked()
            ignore = ignore_check_btn.isChecked()
            dict_combo.setEnabled(not word_checked and not ignore)
            field_combo.setEnabled(not word_checked and not ignore)
            skip_check_btn.setEnabled(not word_checked and not ignore)
            cloze_check_btn.setEnabled(not word_checked and not ignore)

        ignore_check_btn.stateChanged.connect(ignore_check_changed)
        ignore_check_btn.clicked.connect(self.ignore_all_update)
        # skip
        skip_check_btn.clicked.connect(self.skip_all_update)

        # dict
        def dict_combo_changed(index):
            '''dict combo box index changed'''
            self.fill_field_combo_options(
                field_combo, dict_combo.currentText(),
                dict_combo.itemData(index), field_combo.currentText(),
                field_combo.itemData(field_combo.currentIndex()))

        dict_combo.currentIndexChanged.connect(dict_combo_changed)

        self.dicts_layout.addWidget(word_check_btn, i + 1, 0)
        self.dicts_layout.addWidget(ignore_check_btn, i + 1, 1)
        self.dicts_layout.addWidget(dict_combo, i + 1, 2)
        self.dicts_layout.addWidget(field_combo, i + 1, 3)
        self.dicts_layout.addWidget(skip_check_btn, i + 1, 4)
        self.dicts_layout.addWidget(cloze_check_btn, i + 1, 5)

        self._options.append({
            'model': {
                'fld_name': fld_name,
                'fld_ord': fld_ord
            },
            'word_check_btn': word_check_btn,
            'dict_combo': dict_combo,
            'field_combo': field_combo,
            'ignore_check_btn': ignore_check_btn,
            'skip_check_btn': skip_check_btn,
            'cloze_check_btn': cloze_check_btn
        })

    def fill_dict_combo_options(self, dict_combo, current_unique, services):
        '''setup dict combo box'''
        dict_combo.clear()

        # local dict service
        for service in services['local']:
            dict_combo.addItem(service['title'], userData=service['unique'])

        # hr
        if len(services['local']) > 0:
            dict_combo.insertSeparator(dict_combo.count())

        # web dict service
        for service in services['web']:
            dict_combo.addItem(service['title'], userData=service['unique'])

        def set_dict_combo_index():
            dict_combo.setCurrentIndex(0)
            if current_unique:
                for i in range(dict_combo.count()):
                    if dict_combo.itemData(i) == current_unique:
                        dict_combo.setCurrentIndex(i)
                        return True
            return False

        return set_dict_combo_index()

    def fill_field_combo_options(self, field_combo, dict_combo_text,
                                 dict_combo_itemdata, dict_fld_name,
                                 dict_fld_ord):
        '''setup field combobox'''
        field_combo.clear()
        field_combo.setEditable(False)
        # if dict_combo_text in _sl('NOT_DICT_FIELD'):
        #    field_combo.setEnabled(False)
        # el
        if dict_combo_text in _sl('MDX_SERVER'):
            text = dict_fld_name if dict_fld_name else 'http://'
            field_combo.setEditable(True)
            field_combo.setEditText(text)
            field_combo.setFocus(Qt.MouseFocusReason)  # MouseFocusReason
        else:
            unique = dict_combo_itemdata
            service = service_pool.get(unique)
            # problem
            field_combo.setCurrentIndex(0)
            if service and service.support and service.fields:
                for i, each in enumerate(service.fields):
                    field_combo.addItem(each, userData=i)
                    if each == dict_fld_name or i == dict_fld_ord:
                        field_combo.setCurrentIndex(i)
            service_pool.put(service)

    @property
    def data(self):
        if not self._was_built:
            return self._conf
        maps = []
        for row in self._options:
            maps.append({
                'fld_name':
                row['model']['fld_name'],
                'fld_ord':
                row['model']['fld_ord'],
                'word_checked':
                row['word_check_btn'].isChecked(),
                'dict_name':
                row['dict_combo'].currentText().strip(),
                'dict_unique':
                row['dict_combo'].itemData(row['dict_combo'].currentIndex()),
                'dict_fld_name':
                row['field_combo'].currentText().strip(),
                'dict_fld_ord':
                row['field_combo'].itemData(row['field_combo'].currentIndex()),
                'ignore':
                row['ignore_check_btn'].isChecked(),
                'skip_valued':
                row['skip_check_btn'].isChecked(),
                'cloze_word':
                row['cloze_check_btn'].isChecked()
            })
        return maps

    def ignore_all_check_changed(self):
        b = self.ignore_all_check_btn.isChecked()
        for row in self._options:
            row['ignore_check_btn'].setChecked(b)

    def skip_all_check_changed(self):
        b = self.skip_all_check_btn.isChecked()
        for row in self._options:
            row['skip_check_btn'].setChecked(b)

    def ignore_all_update(self):
        b = True
        for row in self._options:
            if not row['ignore_check_btn'].isChecked():
                b = False
                break
        self.ignore_all_check_btn.setChecked(b)

    def skip_all_update(self):
        b = True
        for row in self._options:
            if not row['skip_check_btn'].isChecked():
                b = False
                break
        self.skip_all_check_btn.setChecked(b)


class CTabBar(QTabBar):
    def __init__(self, parent=None):
        super(CTabBar, self).__init__(parent)
        # style
        self.setTabsClosable(True)
        self.setMovable(False)
        self.setExpanding(False)
        self.setDrawBase(False)
        # edit
        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setMaxLength(20)
        self._editor.editingFinished.connect(self.handleEditingFinished)
        self._editor.installEventFilter(self)

    def eventFilter(self, widget, event):
        bhide = False
        if event.type() == QEvent.MouseButtonPress:
            if not self._editor.geometry().contains(event.globalPos()):
                bhide = True
        if not bhide:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    bhide = True
        if bhide:
            self.hideEditor()
            return True
        return QTabBar.eventFilter(self, widget, event)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index >= 0:
            self.editTab(index)

    def editTab(self, index):
        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
        self._editor.setText(self.tabText(index))
        if not self._editor.isVisible():
            self._editor.show()
        self._editor.selectAll()
        self._editor.setEnabled(True)
        self._editor.setFocus()

    def hideEditor(self):
        if self._editor.isVisible():
            self._editor.setEnabled(False)
            self._editor.clearFocus()
            self._editor.hide()

    def handleEditingFinished(self):
        index = self.currentIndex()
        if index >= 0:
            self.hideEditor()
            if self._editor.text():
                self.setTabText(index, self._editor.text())
