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

import sys
import inspect
import os
from hashlib import md5

from .base import LocalService, MdxService, StardictService, WebService, service_wrap
from ..context import config
from ..utils import importlib


reload(sys)
sys.setdefaultencoding('utf8')


class ServiceManager(object):
    """
    Query service class manager
    """

    def __init__(self):
        self.update_services()

    @property
    def services(self):
        return self.web_services + self.local_services

    # def start_all(self):
    #     self.fetch_headers()
        # make all local services available
        # for service in self.local_services:
        #     if not service.index(only_header=True):
        #         self.local_services.remove(service)

    def update_services(self):
        self.web_services, self.local_custom_services = self._get_services_from_files()
        self.local_services = self._get_available_local_services()
        # self.fetch_headers()
        # combine the customized local services into local services
        self.local_services = self.local_services + self.local_custom_services

    def get_service(self, unique):
        # webservice unique: class name
        # mdxservice unique: dict filepath
        for each in self.services:
            if each.__unique__ == unique:
                #cls = getattr(each,"__class__")
                service = each()
                service.unique = unique
                return service

    def get_service_action(self, service, label):
        for each in service.fields:
            if each.label == label:
                return each

    def _get_services_from_files(self, *args):
        """
        get service from service packages, available type is
        WebService, LocalService
        """
        service_path = u'dict'
        web_services, local_custom_services = list(), list()
        mypath = os.path.join(os.path.dirname(os.path.realpath(__file__)), service_path)
        files = [f for f in os.listdir(mypath)
                 if f not in ('__init__.py') and not f.endswith('.pyc') and not os.path.isdir(mypath+os.sep+f)]
        base_class = (WebService, LocalService,
                      MdxService, StardictService)

        for f in files:
            #try:
            module = importlib.import_module( 
                u'.%s.%s' % (service_path, os.path.splitext(f)[0]), 
                __package__
            )
            for name, cls in inspect.getmembers(module, predicate=inspect.isclass):
                if cls in base_class:
                    continue
                #try:
                #service = cls(*args)
                service = service_wrap(cls, *args)
                service.__unique__ = name
                if issubclass(cls, WebService):
                    web_services.append(service)
                    # get the customized local services
                if issubclass(cls, LocalService):
                    local_custom_services.append(service)
                #except Exception:
                    # exclude the local service whose path has error.
                #    pass
            #except ImportError:
            #   continue
        return web_services, local_custom_services

    def _get_available_local_services(self):
        '''
        available local dictionary services
        '''
        local_services = list()
        for each in config.dirs:
            for dirpath, dirnames, filenames in os.walk(each):
                for filename in filenames:
                    service = None
                    dict_path = os.path.join(dirpath, filename)
                    #MDX
                    if MdxService.check(dict_path):
                        service = service_wrap(MdxService, dict_path)
                        service.__unique__ = md5(dict_path).hexdigest()
                        local_services.append(service)
                    #Stardict    
                    if StardictService.check(dict_path):
                        service = service_wrap(StardictService, dict_path)
                        service.__unique__ = md5(dict_path).hexdigest()
                        local_services.append(service)
                # support mdx dictionary and stardict format dictionary
        return local_services
