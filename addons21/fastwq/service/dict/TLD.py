#-*- coding:utf-8 -*-
import os
import re
import random
from ..base import *

DICT_PATH = u"/Users/brian/Documents/mdx/The Little Dict/TLD.mdx" # u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'


@register([u'本地词典-The Little Dict', u'The Little Dict'])
class TLD(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'TLD'):
                    dict_path = service.dict_path
                    break
        super(TLD, self).__init__(dict_path)

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


    @export('iWeb_Rank')
    def iweb_rank(self):
        m = re.findall(r'<div class="\s*.*<\/div>', self.get_html_all())
        if m:
            soup = parse_html(m[0])
            el_list = soup.findAll('div', {'class':'iweb'})
            if el_list:
                rank_temp = el_list[0].findAll('span',{'class':'rank'})
                if rank_temp:
                    rank=[]
                    for i in rank_temp:
                        rank.append(int(i.contents[0]))
                    return str(min(rank))
        return ''

    @export('Chinese_def')
    def chinese_def(self):
        m = re.findall(r'<div class="\s*.*<\/div>', self.get_html_all())
        if m:
            soup = parse_html(m[0])

            el_list = soup.findAll('div', {'class':'coca2'})
            def_distribution = ''
            if el_list:
                def_distribution = str(el_list[0])
            el_list = soup.findAll('div', {'class':'gdc'})
            cn_def = ''
            if el_list:
                cn_def = str(el_list[0])
                return def_distribution + cn_def
        return ''
