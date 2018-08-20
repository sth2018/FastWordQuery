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

from aqt.qt import *
from .base import Dialog, WIDGET_SIZE
from ..context import config
from ..lang import _


__all__ = ['SettingDialog']


class SettingDialog(Dialog):
    '''
    Setting window, some golbal params for query function.
    '''

    def __init__(self, parent, title=u'Setting'):
        super(SettingDialog, self).__init__(parent, title)
        self.setFixedWidth(400)
        self.check_force_update = None
        self.check_ignore_accents = None
        self.check_auto_update = None
        self.input_thread_number = None
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

        check_auto_update = QCheckBox(_("AUTO_UPDATE"))
        check_auto_update.setChecked(config.auto_update)
        layout.addWidget(check_auto_update)
        layout.addSpacing(10)

        check_ighore_mdx_wordcase = QCheckBox(_("IGNORE_MDX_WORDCASE"))
        check_ighore_mdx_wordcase.setChecked(config.ignore_mdx_wordcase)
        layout.addWidget(check_ighore_mdx_wordcase)
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
        self.check_auto_update = check_auto_update
        self.check_ighore_mdx_wordcase = check_ighore_mdx_wordcase
        self.input_thread_number = input_thread_number

        layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.setLayout(layout)

    def accept(self):
        self.save()
        super(SettingDialog, self).accept()
    
    def save(self):
        data = {
            'force_update': self.check_force_update.isChecked(),
            'ignore_accents': self.check_ignore_accents.isChecked(),
            'auto_update': self.check_auto_update.isChecked(),
            'ignore_mdx_wordcase': self.check_ighore_mdx_wordcase.isChecked(),
            'thread_number': self.input_thread_number.value(),
        }
        config.update(data)
        