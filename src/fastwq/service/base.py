#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 ST.Huang <wenhonghuang@gmail.com>
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
# use ntpath module to ensure the windows-style (e.g. '\\LDOCE.css')
# path can be processed on Unix platform.
# However, anki version on mac platforms doesn't including this package?
# import ntpath
import re
import shutil
import sqlite3
import urllib
import urllib2
import zlib
import random
from collections import defaultdict
from functools import wraps

import cookielib
from ..context import config
from ..libs import MdxBuilder, StardictBuilder
from ..utils import MapDict, wrap_css
from ..libs.bs4 import BeautifulSoup

try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading


def register(label):
    """register the dict service with a label, which will be shown in the dicts list."""
    def _deco(cls):
        cls.__register_label__ = label
        return cls
    return _deco


def export(label, index):
    """export dict field function with a label, which will be shown in the fields list."""
    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            res = fld_func(cls, *args, **kwargs)
            return QueryResult(result=res) if not isinstance(res, QueryResult) else res
        _deco.__export_attrs__ = (label, index)
        return _deco
    return _with


def copy_static_file(filename, new_filename=None, static_dir='static'):
    """
    copy file in static directory to media folder
    """
    abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           static_dir,
                           filename)
    shutil.copy(abspath, new_filename if new_filename else filename)


def with_styles(**styles):
    """
    cssfile: specify the css file in static folder
    css: css strings
    js: js strings
    jsfile: specify the js file in static folder
    """
    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            res = fld_func(cls, *args, **kwargs)
            cssfile, css, jsfile, js, need_wrap_css, class_wrapper =\
                styles.get('cssfile', None),\
                styles.get('css', None),\
                styles.get('jsfile', None),\
                styles.get('js', None),\
                styles.get('need_wrap_css', False),\
                styles.get('wrap_class', '')

            def wrap(html, css_obj, is_file=True):
                # wrap css and html
                if need_wrap_css and class_wrapper:
                    html = u'<div class="{}">{}</div>'.format(
                        class_wrapper, html)
                    return html, wrap_css(css_obj, is_file=is_file, class_wrapper=class_wrapper)[0]
                return html, css_obj

            if cssfile:
                new_cssfile = cssfile if cssfile.startswith('_') \
                    else u'_' + cssfile
                # copy the css file to media folder
                copy_static_file(cssfile, new_cssfile)
                # wrap the css file
                res, new_cssfile = wrap(res, new_cssfile)
                res = u'<link type="text/css" rel="stylesheet" href="{0}" />{1}'.format(
                    new_cssfile, res)
            if css:
                res, css = wrap(res, css, is_file=False)
                res = u'<style>{0}</style>{1}'.format(css, res)

            if not isinstance(res, QueryResult):
                return QueryResult(result=res, jsfile=jsfile, js=js)
            else:
                res.set_styles(jsfile=jsfile, js=js)
                return res
        return _deco
    return _with

# BS4资源锁，防止程序卡死
BS_LOCKS = [_threading.Lock(), _threading.Lock()]

def parseHtml(html):
    '''
    使用BS4解析html
    '''
    lock = BS_LOCKS[random.randrange(0, len(BS_LOCKS) - 1, 1)]
    lock.acquire()
    soup = BeautifulSoup(html, 'html.parser')
    lock.release()
    return soup


class Service(object):
    '''service base class'''

    def __init__(self):
        self.cache = defaultdict(defaultdict)
        self._exporters = self.get_exporters()
        self._fields, self._actions = zip(*self._exporters) \
            if self._exporters else (None, None)
        # query interval: default 500ms
        self.query_interval = 0.5

    def cache_this(self, result):
        self.cache[self.word].update(result)
        return result

    def cached(self, key):
        return (self.word in self.cache) and self.cache[self.word].has_key(key)

    def cache_result(self, key):
        return self.cache[self.word].get(key, u'')

    @property
    def support(self):
        return True
        
    @property
    def fields(self):
        return self._fields

    @property
    def actions(self):
        return self._actions

    @property
    def exporters(self):
        return self._exporters

    def get_exporters(self):
        flds = dict()
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method in methods:
            export_attrs = getattr(method[1], '__export_attrs__', None)
            if export_attrs:
                label, index = export_attrs
                flds.update({int(index): (label, method[1])})
        sorted_flds = sorted(flds)
        return [flds[key] for key in sorted_flds]

    def active(self, action_label, word):
        self.word = word
        # if the service instance is LocalService,
        # then have to build then index.
        #if isinstance(self, LocalService):
        #    if isinstance(self, MdxService) or isinstance(self, StardictService):
        #        self.builder.check_build()

        for each in self.exporters:
            if action_label == each[0]:
                return each[1]()
        return QueryResult.default()

    @staticmethod
    def get_anki_label(filename, type_):
        formats = {'audio': u'[sound:{0}]',
                   'img': u'<img src="{0}">',
                   'video': u'<video controls="controls" width="100%" height="auto" src="{0}"></video>'}
        return formats[type_].format(filename)


class WebService(Service):
    '''web service class'''

    def __init__(self):
        super(WebService, self).__init__()
        self._cookie = cookielib.CookieJar()
        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self._cookie))
        self.query_interval = 1.0

    @property
    def title(self):
        return self.__register_label__

    @property
    def unique(self):
        return self.__class__.__name__

    def get_response(self, url, data=None, headers=None, timeout=10):
        default_headers = {'User-Agent': 'Anki WordQuery',
                           'Accept-Encoding': 'gzip'}
        if headers:
            default_headers.update(headers)

        request = urllib2.Request(url, headers=default_headers)
        try:
            response = self._opener.open(request, data=data, timeout=timeout)
            data = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)
            return data
        except:
            return ''

    @classmethod
    def download(cls, url, filename):
        try:
            return urllib.urlretrieve(url, filename)
        except Exception as e:
            pass


class LocalService(Service):
    """
    本地词典
    """

    def __init__(self, dict_path):
        super(LocalService, self).__init__()
        self.dict_path = dict_path
        self.builder = None
        self.missed_css = set()

    @property
    def support(self):
        return os.path.isfile(self.dict_path)

    @property
    def unique(self):
        return self.dict_path

    @property
    def title(self):
        return self.__register_label__

    @property
    def _filename(self):
        return os.path.splitext(os.path.basename(self.dict_path))[0]

# mdx字典实例集
mdx_builders = defaultdict(dict)

class MdxService(LocalService):
    """
    Mdx本地词典
    """

    def __init__(self, dict_path):
        super(MdxService, self).__init__(dict_path)
        self.html_cache = defaultdict(str)
        self.query_interval = 0.01
        self.styles = []
        if self.support:
            if not mdx_builders.has_key(dict_path) or not mdx_builders[dict_path]:
                mdx_builders[dict_path] = MdxBuilder(dict_path)
            self.builder = mdx_builders[dict_path]

    @property
    def support(self):
        return os.path.isfile(self.dict_path) and self.dict_path.lower().endswith('.mdx')

    @property
    def title(self):
        if config.use_filename or not self.builder._title or self.builder._title.startswith('Title'):
            return self._filename
        else:
            return self.builder['_title']

    @export(u"default", 0)
    def fld_whole(self):
        html = self.get_html()
        js = re.findall(r'<script.*?>.*?</script>', html, re.DOTALL)
        return QueryResult(result=html, js=u'\n'.join(js))

    def _get_definition_mdx(self):
        """根据关键字得到MDX词典的解释"""
        content = self.builder.mdx_lookup(self.word)
        str_content = ""
        if len(content) > 0:
            for c in content:
                str_content += c.replace("\r\n","").replace("entry:/","")

        return str_content

    def _get_definition_mdd(self, word):
        """根据关键字得到MDX词典的媒体"""
        word = word.replace('/', '\\')
        content = self.builder.mdd_lookup(word)
        if len(content) > 0:
            return [content[0]]
        else:
            return []

    def get_html(self):
        """取得self.word对应的html页面"""
        if not self.html_cache[self.word]:
            html = self._get_definition_mdx()
            if html:
                self.html_cache[self.word] = html
        return self.html_cache[self.word]

    def save_file(self, filepath_in_mdx, savepath):
        """从mmd中取出filepath_in_mdx媒体文件并保存到savepath"""
        try:
            bytes_list = self._get_definition_mdd(filepath_in_mdx)
            if bytes_list:
                if not os.path.exists(savepath):
                    with open(savepath, 'wb') as f:
                        f.write(bytes_list[0])
                return savepath
        except sqlite3.OperationalError as e:
            #showInfo(str(e))
            pass
        return ''


class StardictService(LocalService):

    def __init__(self, dict_path):
        super(StardictService, self).__init__(dict_path)
        self.query_interval = 0.05
        if self.support:
            self.builder = StardictBuilder(self.dict_path, in_memory=False)
            self.builder.get_header()

    @property
    def support(self):
        return os.path.isfile(self.dict_path) and self.dict_path.lower().endswith('.ifo')

    @property
    def title(self):
        if config.use_filename or not self.builder.ifo.bookname:
            return self._filename
        else:
            return self.builder.ifo.bookname.decode('utf-8')

    @export(u"default", 0)
    def fld_whole(self):
        #self.builder.check_build()
        try:
            result = self.builder[self.word]
            result = result.strip().replace('\r\n', '<br />')\
                .replace('\r', '<br />').replace('\n', '<br />')
            return QueryResult(result=result)
        except KeyError:
            return QueryResult.default()


class QueryResult(MapDict):
    """Query Result structure"""

    def __init__(self, *args, **kwargs):
        super(QueryResult, self).__init__(*args, **kwargs)
        # avoid return None
        if self['result'] == None:
            self['result'] = ""

    def set_styles(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value

    @classmethod
    def default(cls):
        return QueryResult(result="")
