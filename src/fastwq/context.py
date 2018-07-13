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

import json
from aqt import mw
from .constants import VERSION
from .utils import get_icon


CONFIG_FILENAME = '.fastwqcfg.json'     #Config File Path
APP_ICON = get_icon('wqicon.png')       #Addon Icon


class Config(object):

    """
    Addon Config
    """

    def __init__(self, window):
        self.path = CONFIG_FILENAME
        self.window = window
        self.version = '0'
        self.read()

    @property
    def pmname(self):
        return self.window.pm.name

    def update(self, data):
        """
        Update && Save
        """
        data['version'] = VERSION
        data['%s_last' % self.pmname] = data.get('last_model', self.last_model_id)
        self.data.update(data)
        with open(self.path, 'wb') as f:
            json.dump(self.data, f, indent=4, sort_keys=True)
            f.close()

    def read(self):
        """
        Load from config file
        """
        try:
            with open(self.path, 'rb') as f:
                self.data = json.load(f)
                f.close()
        except:
            self.data = dict()

    def get_maps(self, model_id):
        """
        Query fileds map
        """
        return self.data.get(str(model_id), list())

    @property
    def last_model_id(self):
        return self.data.get('%s_last' % self.pmname, 0)

    @property
    def dirs(self):
        return self.data.get('dirs', list())

    @property
    def use_filename(self):
        return self.data.get('use_filename', True)

    @property
    def export_media(self):
        return self.data.get('export_media', False)

    @property
    def force_update(self):
        return self.data.get('force_update', False)

    @property
    def thread_number(self):
        """
        Query Thread Number
        """
        return self.data.get('thread_number', 16)

    @property
    def last_folder(self):
        """
        last file dialog open path 
        """
        return self.data.get('last_folder', '')

    @property
    def ignore_accents(self):
        '''ignore accents of field in querying'''
        return self.data.get('ignore_accents', False)


config = Config(mw)
