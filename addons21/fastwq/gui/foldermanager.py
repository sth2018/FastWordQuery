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

from aqt.qt import *

from ..context import config
from ..lang import _, _sl
from .base import WIDGET_SIZE, Dialog

__all__ = ['FoldersManageDialog']


class FoldersManageDialog(Dialog):
    '''
    Dictionary folder manager window. add or remove dictionary folders.
    '''

    def __init__(self, parent, title=u'Dictionary Folder Manager'):
        super(FoldersManageDialog, self).__init__(parent, title)
        # self._dict_paths = []
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
            options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dir_:
            self.folders_lst.addItem(dir_)
            config.update({'last_folder': dir_})

    def remove_folder(self):
        item = self.folders_lst.takeItem(self.folders_lst.currentRow())
        del item

    @property
    def dirs(self):
        '''dictionary folders list'''
        return [
            self.folders_lst.item(i).text()
            for i in range(self.folders_lst.count())
        ]

    def accept(self):
        '''ok button clicked'''
        self.save()
        super(FoldersManageDialog, self).accept()

    def save(self):
        '''save config to file'''
        data = {
            'dirs': self.dirs,
            'use_filename': self.chk_use_filename.isChecked(),
            'export_media': self.chk_export_media.isChecked()
        }
        config.update(data)
