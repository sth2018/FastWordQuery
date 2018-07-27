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

from ..utils import Empty, Queue


class ServicePool(object):
    """
    Service instance pool
    """
    def __init__(self, manager):
        self.pools = {}
        self.manager = manager
        
    def get(self, unique):
        queue = self.pools.get(unique, None)
        if queue:
            try:
                return queue.get(True, timeout=0.1)
            except Empty:
                pass
        
        return self.manager.get_service(unique)
    
    def put(self, service):
        if service is None:
            return
        unique = service.unique
        queue = self.pools.get(unique, None)
        if queue == None:
            queue = Queue()
            self.pools[unique] = queue
            
        queue.put(service)
        
    def clean(self):
        self.pools = {}
