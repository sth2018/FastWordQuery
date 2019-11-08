#-*- coding:utf-8 -*-
import os
import re
import random
from ..base import *

DICT_PATH = u"/Users/brian/Documents/mdx/lgmcw_Sound++/SoundMobile.mdx" # u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'


@register([u'本地词典-lgmcw_Sound++', u'lgmcw_Sound++'])
class lgmcw_Sound(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'SoundMobile'):
                    dict_path = service.dict_path
                    break
        super(lgmcw_Sound, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    def get_html_all(self):
        html = self.get_html()
        if not html:
            self.word = self.word.lower()
            html = self.get_html()
            if not html:
                self.word = self.word.capitalize()
                html = self.get_html()
                if not html:
                    self.word = self.word.upper()
                    html = self.get_html()
        return html


    @export('BNC_freq')
    def bnc_freq(self):
        html = self.get_html_all()
        if html:
            freq = re.search(r'<BNC-R>(.*?)</BNC-R>', html)
            if freq:
                return freq[1].strip()
        return ''

    @export('IWEB_freq')
    def iweb_freq(self):
        html = self.get_html_all()
        if html:
            print(html)
            freq = re.search(r'<iWeb-R>(.*?)</iWeb-R>', html)
            if freq:
                return freq[1].strip()
        return ''

    @export('ECO_freq')
    def eco_freq(self):
        html = self.get_html_all()
        if html:
            freq = re.search(r'<ECO-R>(.*?)</ECO-R>', html)
            if freq:
                return freq[1].strip()
        return ''

    @export('COCA_freq')
    def coca_freq(self):
        html = self.get_html_all()
        if html:
            freq = re.search(r'<COCA-R>(.*?)</COCA-R>', html)
            if freq:
                return freq[1].strip()
        return ''
