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

import inspect
import os
from hashlib import md5

from .base import LocalService, MdxService, StardictService, WebService, service_wrap
from ..context import config
from ..utils import importlib


class ServiceManager(object):
    """
    Query service class manager
    """

    def __init__(self):
        self.update_services()

    @property
    def services(self):
        return self.web_services + self.local_services

    def update_services(self):
        self.mdx_services, self.star_dict_services = self._get_available_local_services()
        self.web_services, self.local_custom_services = self._get_services_from_files()
        # combine the customized local services into local services
        self.local_services = self.mdx_services + self.star_dict_services + self.local_custom_services

    def get_service(self, unique):
        # webservice unique: class name
        # mdxservice unique: md5 of dict filepath
        for each in self.services:
            if each.__unique__ == unique:
                service = each()
                service.unique = unique
                return service

    def _get_services_from_files(self, *args):
        """
        get service from service packages, available type is
        WebService, LocalService
        """
        service_path = u'dict'
        web_services, local_custom_services = list(), list()
        mypath = os.path.join(os.path.dirname(os.path.realpath(__file__)), service_path)
        files = [
            f for f in os.listdir(mypath) \
            if f not in ('__init__.py') and \
            f.endswith('.py') and \
            not os.path.isdir(mypath+os.sep+f)
        ]
        base_class = (
            WebService, 
            LocalService,
            MdxService, 
            StardictService
        )
        for f in files:
            #try:
            module = importlib.import_module( 
                u'.%s.%s' % (service_path, os.path.splitext(f)[0]), 
                __package__
            )
            for name, clazz in inspect.getmembers(module, predicate=inspect.isclass):
                if clazz in base_class:
                    continue
                if not(issubclass(clazz, WebService) or issubclass(clazz, LocalService)):
                    continue
                if getattr(clazz, '__register_label__', None) is None:
                    continue
                service = service_wrap(clazz, *args)
                service.__title__ = getattr(clazz, '__register_label__', name)
                service.__unique__ = name
                service.__path__ = os.path.join(mypath, f)
                if issubclass(clazz, WebService):
                    web_services.append(service)
                    # get the customized local services
                if issubclass(clazz, LocalService):
                    local_custom_services.append(service)
        web_services = sorted(web_services, key=lambda service: service.__title__)
        local_custom_services = sorted(local_custom_services, key=lambda service: service.__title__)
        return web_services, local_custom_services

    def _get_available_local_services(self):
        '''
        available local dictionary services
        '''
        mdx_services = list()
        star_dict_services = list()
        for each in config.dirs:
            for dirpath, dirnames, filenames in os.walk(each):
                for filename in filenames:
                    service = None
                    dict_path = os.path.join(dirpath, filename)
                    #MDX
                    if MdxService.check(dict_path):
                        service = service_wrap(MdxService, dict_path)
                        service.__unique__ = md5(str(dict_path).encode('utf-8')).hexdigest()
                        mdx_services.append(service)
                    #Stardict    
                    if StardictService.check(dict_path):
                        service = service_wrap(StardictService, dict_path)
                        service.__unique__ = md5(str(dict_path).encode('utf-8')).hexdigest()
                        star_dict_services.append(service)
                # support mdx dictionary and stardict format dictionary
        return mdx_services, star_dict_services
