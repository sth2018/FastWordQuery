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

from PyQt4 import QtCore, QtGui
import anki
import aqt
import aqt.models
from aqt import mw
from aqt.studydeck import StudyDeck
from .base import Dialog, WIDGET_SIZE
from .setting import SettingDialog
from ..context import config
from ..lang import _, _sl
from ..service import service_manager, service_pool
from ..utils import get_model_byId
from ..constants import Endpoint


__all__ = ['OptionsDialog']


class OptionsDialog(Dialog):
    '''
    query options window
    setting query dictionary and fileds
    '''

    __slot__ = [
        'begore_build',
        'after_build'
    ]

    def __init__(self, parent, title=u'Options', model_id = -1):
        super(OptionsDialog, self).__init__(parent, title)
        self.connect(self, QtCore.SIGNAL('before_build'), self._before_build, QtCore.Qt.QueuedConnection)
        self.connect(self, QtCore.SIGNAL('after_build'), self._after_build, QtCore.Qt.QueuedConnection)
        # initlizing info
        self.main_layout = QtGui.QVBoxLayout()
        self.loading_label = QtGui.QLabel(_('INITLIZING_DICT'))
        self.main_layout.addWidget(self.loading_label, 0, QtCore.Qt.AlignCenter)
        #self.loading_layout.addLayout(models_layout)
        self.setLayout(self.main_layout)
        #initlize properties
        self.___last_checkeds___ = None
        self.___options___ = list()
        self.model_id = model_id if model_id != -1 else config.last_model_id
        self.current_model = None
        # size and signal
        self.resize(WIDGET_SIZE.dialog_width, 4 * WIDGET_SIZE.map_max_height + WIDGET_SIZE.dialog_height_margin)
        self.emit(QtCore.SIGNAL('before_build'))
    
    def _before_build(self):
        for cls in service_manager.services:
            service = service_pool.get(cls.__unique__)
            if service:
                service_pool.put(service)
        self.emit(QtCore.SIGNAL('after_build'))

    def _after_build(self):
        self.main_layout.removeWidget(self.loading_label)
        models_layout = QtGui.QHBoxLayout()
        # add buttons
        mdx_button = QtGui.QPushButton(_('DICTS_FOLDERS'))
        mdx_button.clicked.connect(self.show_fm_dialog)
        self.models_button = QtGui.QPushButton(_('CHOOSE_NOTE_TYPES'))
        self.models_button.clicked.connect(self.btn_models_pressed)
        models_layout.addWidget(mdx_button)
        models_layout.addWidget(self.models_button)
        self.main_layout.addLayout(models_layout)
        # add dicts mapping
        dicts_widget = QtGui.QWidget()
        self.dicts_layout = QtGui.QGridLayout()
        self.dicts_layout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        dicts_widget.setLayout(self.dicts_layout)

        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(dicts_widget)

        self.main_layout.addWidget(scroll_area)
        # add description of radio buttons AND ok button
        bottom_layout = QtGui.QHBoxLayout()
        paras_btn = QtGui.QPushButton(_('SETTINGS'))
        paras_btn.clicked.connect(self.show_paras)
        about_btn = QtGui.QPushButton(_('ABOUT'))
        about_btn.clicked.connect(self.show_about)
        # about_btn.clicked.connect(self.show_paras)
        chk_update_btn = QtGui.QPushButton(_('UPDATE'))
        chk_update_btn.clicked.connect(self.check_updates)
        home_label = QtGui.QLabel(
            '<a href="{url}">User Guide</a>'.format(url=Endpoint.user_guide))
        home_label.setOpenExternalLinks(True)
        # shop_label = QLabel(
        #     '<a href="{url}">Service Shop</a>'.format(url=Endpoint.service_shop))
        # shop_label.setOpenExternalLinks(True)
        btnbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok, QtCore.Qt.Horizontal, self)
        btnbox.accepted.connect(self.accept)
        bottom_layout.addWidget(paras_btn)
        bottom_layout.addWidget(chk_update_btn)
        bottom_layout.addWidget(about_btn)
        bottom_layout.addWidget(home_label)
        # bottom_layout.addWidget(shop_label)
        bottom_layout.addWidget(btnbox)
        #self.setLayout(self.main_layout)
        self.main_layout.addLayout(bottom_layout)
        # init from saved data
        self.current_model = None
        if self.model_id:
            self.current_model = get_model_byId(mw.col.models, self.model_id)
        if self.current_model:
            self.models_button.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'),  self.current_model['name']))
            # build fields -- dicts layout
            self.build_mappings_layout(self.current_model)

    def show_paras(self):
        '''open setting dialog'''
        dialog = SettingDialog(self, u'Setting')
        dialog.exec_()

    def check_updates(self):
        '''check addon version'''
        from .common import check_updates
        check_updates()

    def show_fm_dialog(self):
        '''open folder manager dialog'''
        from .common import show_fm_dialog
        self.save()
        self.close()
        show_fm_dialog(self._parent)

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
            self.build_mappings_layout(self.current_model)

    def build_mappings_layout(self, model):
        '''
        build dictionary、fields etc
        '''
        def clear_layout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        clear_layout(item.layout())

        clear_layout(self.dicts_layout)
        del self.___options___[:]
        self.___last_checkeds___ = None

        labels = ['', '', 'DICTS', 'DICT_FIELDS', '']
        for i, s in enumerate(labels):
            label = QtGui.QLabel(_(s))
            label.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
            self.dicts_layout.addWidget(label, 0, i)

        maps = config.get_maps(model['id'])
        self.radio_group = QtGui.QButtonGroup()
        for i, fld in enumerate(model['flds']):
            ord = fld['ord']
            name = fld['name']
            if maps:
                for j, each in enumerate(maps):
                    if each.get('fld_ord', -1) == ord or each.get('fld_name', '') == name:
                        each['fld_name'] = name
                        each['fld_ord'] = ord
                        self.add_dict_layout(j, **each)
                        break
                else:
                    self.add_dict_layout(i, fld_name=name, fld_ord=ord)
            else:
                self.add_dict_layout(i, fld_name=name, fld_ord=ord)

        #self.setLayout(self.main_layout)
        self.resize(WIDGET_SIZE.dialog_width,
                    max(3, (i + 1)) * WIDGET_SIZE.map_max_height + WIDGET_SIZE.dialog_height_margin)
        self.save()

    def show_models(self):
        '''
        show choose note type window
        '''
        edit = QtGui.QPushButton(anki.lang._("Manage"),
                           clicked=lambda: aqt.models.Models(mw, self))
        ret = StudyDeck(mw, names=lambda: sorted(mw.col.models.allNames()),
                        accept=anki.lang._("Choose"), title=anki.lang._("Choose Note Type"),
                        help="_notes", parent=self, buttons=[edit],
                        cancel=True, geomKey="selectModel")
        if ret.name:
            model = mw.col.models.byName(ret.name)
            self.models_button.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'), ret.name))
            return model

    def fill_dict_combo_options(self, dict_combo, current_unique):
        '''setup dict combo box'''
        dict_combo.clear()
        #dict_combo.addItem(_('NOT_DICT_FIELD'))

        # local dict service
        #dict_combo.insertSeparator(dict_combo.count())
        has_local_service = False
        for cls in service_manager.local_services:
            # combo_data.insert("data", each.label)
            service = service_pool.get(cls.__unique__)
            if service and service.support:
                dict_combo.addItem(
                    service.title, userData=service.unique)
                service_pool.put(service)
                has_local_service = True

        # hr
        if has_local_service:
            dict_combo.insertSeparator(dict_combo.count())
        
        # web dict service
        for cls in service_manager.web_services:
            service = service_pool.get(cls.__unique__)
            if service and service.support:
                dict_combo.addItem(
                    service.title, userData=service.unique)
                service_pool.put(service)

        def set_dict_combo_index():
            #dict_combo.setCurrentIndex(-1)
            dict_combo.setCurrentIndex(0)
            if current_unique:
                for i in range(dict_combo.count()):
                    if dict_combo.itemData(i) == current_unique:
                        dict_combo.setCurrentIndex(i)
                        break
            
        set_dict_combo_index()

    def fill_field_combo_options(self, field_combo, dict_combo_text, dict_combo_itemdata, dict_fld_name, dict_fld_ord):
        '''setup field combobox'''
        field_combo.clear()
        field_combo.setEditable(False)
        #if dict_combo_text in _sl('NOT_DICT_FIELD'):
        #    field_combo.setEnabled(False)
        #el
        if dict_combo_text in _sl('MDX_SERVER'):
            text = dict_fld_name if dict_fld_name else 'http://'
            field_combo.setEditable(True)
            field_combo.setEditText(text)
            field_combo.setFocus(QtCore.Qt.MouseFocusReason)  # MouseFocusReason
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

    def add_dict_layout(self, i, **kwargs):
        """
        add dictionary fields row
        """
        word_checked = i == 0

        fld_name, fld_ord = (
            kwargs.get('fld_name', ''),                                 #笔记类型的字段名
            kwargs.get('fld_ord', ''),                                  #笔记类型的字段编号
        )

        dict_name, dict_unique, dict_fld_name, dict_fld_ord = (
            kwargs.get('dict_name', ''),                                #字典名
            kwargs.get('dict_unique', ''),                              #字典ID
            kwargs.get('dict_fld_name', ''),                            #对应字典的字段名
            kwargs.get('dcit_fld_ord', 0)                               #对应字典的字段编号
        )

        ignore, skip = (
            kwargs.get('ignore', True),                                 #忽略标志
            kwargs.get('skip_valued', True),                            #略过有值项标志
        )
        # check
        word_check_btn = QtGui.QRadioButton(fld_name)
        word_check_btn.setMinimumSize(WIDGET_SIZE.map_fld_width, 0)
        word_check_btn.setMaximumSize(
            WIDGET_SIZE.map_fld_width,
            WIDGET_SIZE.map_max_height
        )
        word_check_btn.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        word_check_btn.setCheckable(True)
        word_check_btn.setChecked(word_checked)
        self.radio_group.addButton(word_check_btn)
        # dict combox
        dict_combo = QtGui.QComboBox()
        dict_combo.setMinimumSize(WIDGET_SIZE.map_dictname_width, 0)
        dict_combo.setFocusPolicy(
            QtCore.Qt.TabFocus | QtCore.Qt.ClickFocus | QtCore.Qt.StrongFocus | QtCore.Qt.WheelFocus
        )
        dict_combo.setEnabled(not word_checked and not ignore)
        self.fill_dict_combo_options(dict_combo, dict_unique)
        dict_unique = dict_combo.itemData(dict_combo.currentIndex())
        # field combox
        field_combo = QtGui.QComboBox()
        field_combo.setMinimumSize(WIDGET_SIZE.map_dictfield_width, 0)
        field_combo.setEnabled(not word_checked and not ignore)
        self.fill_field_combo_options(field_combo, dict_name, dict_unique, dict_fld_name, dict_fld_ord)

        # ignore
        ignore_check_btn = QtGui.QCheckBox(_("NOT_DICT_FIELD"))
        ignore_check_btn.setEnabled(not word_checked)
        ignore_check_btn.setChecked(ignore)

        # Skip valued
        skip_check_btn = QtGui.QCheckBox(_("SKIP_VALUED"))
        skip_check_btn.setEnabled(not word_checked and not ignore)
        skip_check_btn.setChecked(skip)

        # events
        # word
        def radio_btn_checked():
            if self.___last_checkeds___:
                self.___last_checkeds___[0].setEnabled(True)
                ignore = self.___last_checkeds___[0].isChecked()
                for i in range(1, len(self.___last_checkeds___)):
                    self.___last_checkeds___[i].setEnabled(not ignore)

            word_checked = word_check_btn.isChecked()
            ignore_check_btn.setEnabled(not word_checked)
            ignore = ignore_check_btn.isChecked()
            dict_combo.setEnabled(not word_checked and not ignore)
            field_combo.setEnabled(not word_checked and not ignore)
            skip_check_btn.setEnabled(not word_checked and not ignore)
            if word_checked:
                self.___last_checkeds___ = [
                    ignore_check_btn, dict_combo, 
                    field_combo, skip_check_btn
                ]
        word_check_btn.clicked.connect(radio_btn_checked)
        if word_checked: 
            self.___last_checkeds___ = None
            radio_btn_checked()
        # ignor
        def ignore_check_changed():
            ignore = not ignore_check_btn.isChecked()
            dict_combo.setEnabled(ignore)
            field_combo.setEnabled(ignore)
            skip_check_btn.setEnabled(ignore)
        ignore_check_btn.clicked.connect(ignore_check_changed)
        # dict
        def dict_combo_changed(index):
            '''dict combo box index changed'''
            self.fill_field_combo_options(
                field_combo,
                dict_combo.currentText(),
                dict_combo.itemData(index),
                field_combo.currentText(),
                field_combo.itemData(field_combo.currentIndex())
            )
        dict_combo.currentIndexChanged.connect(dict_combo_changed)

        self.dicts_layout.addWidget(word_check_btn, i + 1, 0)
        self.dicts_layout.addWidget(ignore_check_btn, i + 1, 1)
        self.dicts_layout.addWidget(dict_combo, i + 1, 2)
        self.dicts_layout.addWidget(field_combo, i + 1, 3)
        self.dicts_layout.addWidget(skip_check_btn, i + 1, 4)

        self.___options___.append({
            'model': {'fld_name': fld_name, 'fld_ord': fld_ord},
            'word_check_btn': word_check_btn, 
            'dict_combo': dict_combo, 
            'field_combo': field_combo, 
            'ignore_check_btn': ignore_check_btn, 
            'skip_check_btn': skip_check_btn
        })

    def save(self):
        '''save config to file'''
        if not self.current_model:
            return
        data = dict()
        maps = []
        for row in self.___options___:
            maps.append({
                'fld_name': row['model']['fld_name'],
                'fld_ord': row['model']['fld_ord'],
                'word_checked': row['word_check_btn'].isChecked(),
                'dict_name': row['dict_combo'].currentText().strip(),
                'dict_unique': row['dict_combo'].itemData(row['dict_combo'].currentIndex()),
                'dict_fld_name': row['field_combo'].currentText().strip(),
                'dict_fld_ord': row['field_combo'].itemData(row['field_combo'].currentIndex()),
                'ignore': row['ignore_check_btn'].isChecked(),
                'skip_valued': row['skip_check_btn'].isChecked()
            })
        current_model_id = str(self.current_model['id'])
        data[current_model_id] = maps
        data['last_model'] = self.current_model['id']
        config.update(data)
