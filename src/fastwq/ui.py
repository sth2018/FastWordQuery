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

import os
import sys
import json
from collections import namedtuple

import anki
import aqt
import aqt.models
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo
from .constants import VERSION, Endpoint, Template
from .context import APP_ICON, config
from .lang import _, _sl
from .service import service_manager, service_pool
from .utils import MapDict, get_icon, get_model_byId, get_ord_from_fldname

DICT_COMBOS, DICT_FILED_COMBOS, ALL_COMBOS = [0, 1, 2]

widget_size = namedtuple('WidgetSize', ['dialog_width', 'dialog_height_margin', 'map_min_height',
                                        'map_max_height', 'map_fld_width', 'map_dictname_width',
                                        'map_dictfield_width'])(650, 120, 0, 31, 100, 130, 130)

class ParasDialog(QDialog):
    '''
    Setting window, some golbal params for query function.
    '''

    def __init__(self, parent=0):
        super(ParasDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        self.parent = parent
        self.setWindowTitle(u"Settings")
        self.setFixedWidth(400)

        self.check_force_update = None
        self.input_thread_number = None
        # self.setFixedHeight(300)
        
        self.build()

    def build(self):
        layout = QVBoxLayout()

        check_force_update = QCheckBox(_("FORCE_UPDATE"))
        check_force_update.setChecked(config.force_update)
        layout.addWidget(check_force_update)
        layout.addSpacing(10)

        check_ignore_accents = QCheckBox(_("IGNORE_ACCENTS"))
        check_ignore_accents.setChecked(config.ignore_accents)
        layout.addWidget(check_ignore_accents)
        layout.addSpacing(10)

        hbox = QHBoxLayout()
        input_thread_number = QSpinBox(parent=self)
        input_thread_number.setRange(1, 120)
        input_thread_number.setValue(config.thread_number)
        input_label = QLabel(_("THREAD_NUMBER") + ":", parent=self)
        hbox.addWidget(input_label)
        hbox.setStretchFactor(input_label, 1)
        hbox.addWidget(input_thread_number)
        hbox.setStretchFactor(input_thread_number, 2)
        layout.addLayout(hbox)

        buttonBox = QDialogButtonBox(parent=self)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept) # 确定
        
        layout.addSpacing(48)
        layout.addWidget(buttonBox)
        
        self.check_force_update = check_force_update
        self.check_ignore_accents = check_ignore_accents
        self.input_thread_number = input_thread_number

        layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.setLayout(layout)

    def accept(self):
        self.save()
        self.close()
    
    def save(self):
        data = {
            'force_update': self.check_force_update.isChecked(),
            'ignore_accents': self.check_ignore_accents.isChecked(),
            'thread_number': self.input_thread_number.value()
        }
        config.update(data)


class FoldersManageDialog(QDialog):
    '''
    Dictionary folder manager window. add or remove dictionary folders.
    '''

    def __init__(self, parent=0):
        super(FoldersManageDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        self.parent = parent
        self.setWindowTitle(u"Dictionary Folders Manager")
        self._dict_paths = []
        self.build()

    def build(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+")
        remove_btn = QPushButton("-")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        add_btn.clicked.connect(self.add_folder)
        remove_btn.clicked.connect(self.remove_folder)
        self.folders_lst = QListWidget()
        self.folders_lst.addItems(config.dirs)
        self.chk_use_filename = QCheckBox(_('CHECK_FILENAME_LABEL'))
        self.chk_export_media = QCheckBox(_('EXPORT_MEDIA'))
        self.chk_use_filename.setChecked(config.use_filename)
        self.chk_export_media.setChecked(config.export_media)
        chk_layout = QHBoxLayout()
        chk_layout.addWidget(self.chk_use_filename)
        chk_layout.addWidget(self.chk_export_media)
        btnbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        btnbox.accepted.connect(self.accept)
        layout.addLayout(btn_layout)
        layout.addWidget(self.folders_lst)
        layout.addLayout(chk_layout)
        layout.addWidget(btnbox)
        self.setLayout(layout)

    def add_folder(self):
        dir_ = QFileDialog.getExistingDirectory(
            self,
            caption=u"Select Folder", 
            directory=config.last_folder, 
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if dir_:
            self.folders_lst.addItem(dir_)
            config.update({'last_folder': dir_})

    def remove_folder(self):
        item = self.folders_lst.takeItem(self.folders_lst.currentRow())
        del item

    def find_mdxes(self):
        for each in self.dirs:
            for dirpath, dirnames, filenames in os.walk(each):
                self._dict_paths.extend([os.path.join(dirpath, filename)
                                         for filename in filenames if filename.lower().endswith(u'.mdx')])
        return list(set(self._dict_paths))

    @property
    def dict_paths(self):
        return self.find_mdxes()

    @property
    def dirs(self):
        return [self.folders_lst.item(i).text()
                for i in range(self.folders_lst.count())]

    def save(self):
        data = {
            'dirs': self.dirs,
            'use_filename': self.chk_use_filename.isChecked(),
            'export_media': self.chk_export_media.isChecked()
        }
        config.update(data)


class OptionsDialog(QDialog):
    '''
    query options window
    setting query dictionary and fileds
    '''

    def __init__(self, parent=0, browser=None):
        super(OptionsDialog, self).__init__(parent)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        '''
        self.setWindowFlags(
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinMaxButtonsHint
        )
        '''
        self.parent = parent
        self.browser = browser
        self.connect(self, SIGNAL('before_build'), self._before_build, Qt.QueuedConnection)
        self.connect(self, SIGNAL('after_build'), self._after_build, Qt.QueuedConnection)
        # from PyQt4 import QtCore, QtGui
        self.setWindowIcon(APP_ICON)
        self.setWindowTitle(u"Options")
        # initlizing info
        self.main_layout = QVBoxLayout()
        self.loading_label = QLabel(_('INITLIZING_DICT'))
        self.main_layout.addWidget(self.loading_label, 0, Qt.AlignCenter)
        #self.loading_layout.addLayout(models_layout)
        self.setLayout(self.main_layout)
        #initlize properties
        self.___last_checkeds___ = None
        self.___options___ = list()
        # size and signal
        self.resize(widget_size.dialog_width, 4 * widget_size.map_max_height + widget_size.dialog_height_margin)
        self.emit(SIGNAL('before_build'), self.browser)
    
    def _before_build(self, browser=None):
        for cls in service_manager.services:
            service = service_pool.get(cls.__unique__)
        self.emit(SIGNAL('after_build'), browser)

    def _after_build(self, browser=None):
        self.main_layout.removeWidget(self.loading_label)
        models_layout = QHBoxLayout()
        # add buttons
        mdx_button = QPushButton(_('DICTS_FOLDERS'))
        mdx_button.clicked.connect(self.show_fm_dialog)
        self.models_button = QPushButton(_('CHOOSE_NOTE_TYPES'))
        self.models_button.clicked.connect(self.btn_models_pressed)
        models_layout.addWidget(mdx_button)
        models_layout.addWidget(self.models_button)
        self.main_layout.addLayout(models_layout)
        # add dicts mapping
        dicts_widget = QWidget()
        self.dicts_layout = QGridLayout()
        self.dicts_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        dicts_widget.setLayout(self.dicts_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(dicts_widget)

        self.main_layout.addWidget(scroll_area)
        # add description of radio buttons AND ok button
        bottom_layout = QHBoxLayout()
        paras_btn = QPushButton(_('SETTINGS'))
        paras_btn.clicked.connect(self.show_paras)
        about_btn = QPushButton(_('ABOUT'))
        about_btn.clicked.connect(self.show_about)
        # about_btn.clicked.connect(self.show_paras)
        chk_update_btn = QPushButton(_('UPDATE'))
        chk_update_btn.clicked.connect(check_updates)
        home_label = QLabel(
            '<a href="{url}">User Guide</a>'.format(url=Endpoint.user_guide))
        home_label.setOpenExternalLinks(True)
        # shop_label = QLabel(
        #     '<a href="{url}">Service Shop</a>'.format(url=Endpoint.service_shop))
        # shop_label.setOpenExternalLinks(True)
        btnbox = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
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
        model_id = config.last_model_id
        if browser:
            for note_id in browser.selectedNotes():
                note = browser.mw.col.getNote(note_id)
                model_id = note.model()['id']
                break
        if model_id:
            self.current_model = get_model_byId(mw.col.models, model_id)
        if self.current_model:
            self.models_button.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'),  self.current_model['name']))
            # build fields -- dicts layout
            self.build_mappings_layout(self.current_model)

    def show_paras(self):
        dialog = ParasDialog(self)
        dialog.exec_()

    def show_fm_dialog(self):
        self.save()
        self.close()
        show_fm_dialog(self.browser)

    def show_about(self):
        QMessageBox.about(self, _('ABOUT'), Template.tmpl_about)

    def accept(self):
        self.save()
        self.close()

    def btn_models_pressed(self):
        self.save()
        self.current_model = self.show_models()
        if self.current_model:
            self.build_mappings_layout(self.current_model)

    def build_mappings_layout(self, model):

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

        labels = ['', '', 'DICTS', 'DICT_FIELDS', '']
        for i, s in enumerate(labels):
            label = QLabel(_(s))
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.dicts_layout.addWidget(label, 0, i)

        maps = config.get_maps(model['id'])
        self.radio_group = QButtonGroup()
        for i, fld in enumerate(model['flds']):
            ord = fld['ord']
            name = fld['name']
            if maps:
                for j, each in enumerate(maps):
                    if each.get('fld_ord', -1) == ord:
                        self.add_dict_layout(j, fld_name=name, **each)
                        break
                else:
                    self.add_dict_layout(i, fld_name=name)
            else:
                self.add_dict_layout(i, fld_name=name)

        #self.setLayout(self.main_layout)
        self.resize(widget_size.dialog_width,
                    max(3, (i + 1)) * widget_size.map_max_height + widget_size.dialog_height_margin)
        self.save()

    def show_models(self):
        edit = QPushButton(anki.lang._("Manage"),
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

    def fill_dict_combo_options(self, dict_combo, current_text):
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
            for i in range(dict_combo.count()):
                #if current_text in _sl('NOT_DICT_FIELD'):
                #    dict_combo.setCurrentIndex(0)
                #    return False
                if dict_combo.itemText(i) == current_text:
                    dict_combo.setCurrentIndex(i)
            
        set_dict_combo_index()

    def fill_field_combo_options(self, field_combo, dict_combo_text, dict_combo_itemdata, field_combo_text):
        '''setup field combobox'''
        field_combo.clear()
        field_combo.setEditable(False)
        #if dict_combo_text in _sl('NOT_DICT_FIELD'):
        #    field_combo.setEnabled(False)
        #el
        if dict_combo_text in _sl('MDX_SERVER'):
            text = field_combo_text if field_combo_text else 'http://'
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
                    field_combo.addItem(each)
                    if each == field_combo_text:
                        field_combo.setCurrentIndex(i)
            service_pool.put(service)

    def add_dict_layout(self, i, **kwargs):
        """
        kwargs:
        word_checked  dict  fld_name dict_field
        """
        word_checked = i == 0
        dict_name, dict_unique, fld_name, dict_field, ignore, skip = (
            kwargs.get('dict', ''),
            kwargs.get('dict_unique', ''),
            kwargs.get('fld_name', ''),
            kwargs.get('dict_field', ''),
            kwargs.get('ignore', False),
            kwargs.get('skip_valued', False),
        )
        # check
        word_check_btn = QRadioButton(fld_name)
        word_check_btn.setMinimumSize(widget_size.map_fld_width, 0)
        word_check_btn.setMaximumSize(
            widget_size.map_fld_width,
            widget_size.map_max_height
        )
        word_check_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        word_check_btn.setCheckable(True)
        word_check_btn.setChecked(word_checked)
        self.radio_group.addButton(word_check_btn)
        # dict combox
        dict_combo = QComboBox()
        dict_combo.setMinimumSize(widget_size.map_dictname_width, 0)
        dict_combo.setFocusPolicy(
            Qt.TabFocus | Qt.ClickFocus | Qt.StrongFocus | Qt.WheelFocus
        )
        dict_combo.setEnabled(not word_checked and not ignore)
        self.fill_dict_combo_options(dict_combo, dict_name)
        # field combox
        field_combo = QComboBox()
        field_combo.setMinimumSize(widget_size.map_dictfield_width, 0)
        field_combo.setEnabled(not word_checked and not ignore)
        self.fill_field_combo_options(field_combo, dict_name, dict_unique, dict_field)

        # ignore
        check_ignore = QCheckBox(_("NOT_DICT_FIELD"))
        check_ignore.setEnabled(not word_checked)
        check_ignore.setChecked(ignore)

        # Skip valued
        check_skip = QCheckBox(_("SKIP_VALUED"))
        check_skip.setEnabled(not word_checked and not ignore)
        check_skip.setChecked(skip)

        # events
        # word
        def radio_btn_checked():
            if self.___last_checkeds___:
                self.___last_checkeds___[0].setEnabled(True)
                ignore = self.___last_checkeds___[0].isChecked()
                for i in range(1, len(self.___last_checkeds___)):
                    self.___last_checkeds___[i].setEnabled(not ignore)

            word_checked = word_check_btn.isChecked()
            check_ignore.setEnabled(not word_checked)
            ignore = check_ignore.isChecked()
            dict_combo.setEnabled(not word_checked and not ignore)
            field_combo.setEnabled(not word_checked and not ignore)
            check_skip.setEnabled(not word_checked and not ignore)
            if word_checked:
                self.___last_checkeds___ = [
                    check_ignore, dict_combo, 
                    field_combo, check_skip
                ]
        word_check_btn.clicked.connect(radio_btn_checked)
        if word_checked: 
            self.___last_checkeds___ = None
            radio_btn_checked()
        # ignor
        def ignore_check_changed():
            ignore = not check_ignore.isChecked()
            dict_combo.setEnabled(ignore)
            field_combo.setEnabled(ignore)
            check_skip.setEnabled(ignore)
        check_ignore.clicked.connect(ignore_check_changed)
        # dict
        def dict_combo_changed(index):
            '''dict combo box index changed'''
            self.fill_field_combo_options(
                field_combo,
                dict_combo.currentText(),
                dict_combo.itemData(index),
                field_combo.currentText()
            )
        dict_combo.currentIndexChanged.connect(dict_combo_changed)

        self.dicts_layout.addWidget(word_check_btn, i + 1, 0)
        self.dicts_layout.addWidget(check_ignore, i + 1, 1)
        self.dicts_layout.addWidget(dict_combo, i + 1, 2)
        self.dicts_layout.addWidget(field_combo, i + 1, 3)
        self.dicts_layout.addWidget(check_skip, i + 1, 4)

        self.___options___.append([
                word_check_btn,
                dict_combo,
                field_combo,
                check_ignore,
                check_skip
            ]
        )

    def save(self):
        if not self.current_model:
            return
        data = dict()
        maps = [
            {
                "word_checked": x[0].isChecked(),
                "dict": x[1].currentText().strip(),
                "dict_unique": x[1].itemData(x[1].currentIndex()) if x[1].itemData(x[1].currentIndex()) else '',
                "dict_field": x[2].currentText().strip(),
                "fld_ord": get_ord_from_fldname(self.current_model, x[0].text()),
                'ignore': x[3].isChecked(),
                'skip_valued': x[4].isChecked(),
            }
            for x in self.___options___
        ]
        current_model_id = str(self.current_model['id'])
        data[current_model_id] = maps
        data['last_model'] = self.current_model['id']
        config.update(data)


def check_updates():
    '''check add-on last version'''
    try:
        import libs.ankihub
        if not libs.ankihub.update([Endpoint.check_version], False, Endpoint.version):
            showInfo(_('LATEST_VERSION'))
    except:
        showInfo(_('CHECK_FAILURE'))
        pass


def show_options(browser = None):
    '''open options window'''
    parent = mw if browser is None else browser
    config.read()
    opt_dialog = OptionsDialog(parent, browser)
    opt_dialog.activateWindow()
    opt_dialog.raise_()
    opt_dialog.exec_()


def show_fm_dialog(browser = None):
    '''open dictionary folder manager window'''
    parent = mw if browser is None else browser
    fm_dialog = FoldersManageDialog(parent)
    fm_dialog.activateWindow()
    fm_dialog.raise_()
    if fm_dialog.exec_() == QDialog.Accepted:
        dict_paths = fm_dialog.dict_paths
        fm_dialog.save()
        # update local services
        service_manager.update_services()
    # reshow options window
    show_options(browser)
