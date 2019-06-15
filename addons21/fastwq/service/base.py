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

import inspect
import os
import random
# use ntpath module to ensure the windows-style (e.g. '\\LDOCE.css')
# path can be processed on Unix platform.
# However, anki version on mac platforms doesn't including this package?
# import ntpath
import re
import shutil
import sqlite3
import urllib
import zlib
from collections import defaultdict
from functools import wraps
from hashlib import md5, sha1

import requests
from bs4 import BeautifulSoup

from aqt import mw
from aqt.qt import QMutex, QThread

from ..context import config
from ..lang import _cl
from ..libs import MdxBuilder, StardictBuilder
from ..utils import MapDict, wrap_css

try:
    import urllib2
except Exception:
    import urllib.request as urllib2


try:
    from cookielib import CookieJar
except Exception:
    from http.cookiejar import CookieJar


try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading


__all__ = [
    'register', 'export', 'copy_static_file', 'with_styles', 'parse_html', 'service_wrap', 'get_hex_name', 
    'Service', 'WebService', 'LocalService', 'MdxService', 'StardictService', 'QueryResult'
]

_default_ua = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'


def get_hex_name(prefix, val, suffix):
    ''' get sha1 hax name '''
    hex_digest = sha1(val.encode('utf-8')).hexdigest().lower()
    name = '.'.join(['-'.join([prefix, hex_digest[:8], hex_digest[8:16], hex_digest[16:24], hex_digest[24:32], hex_digest[32:], ]), suffix, ])
    return name


def _is_method_or_func(object):
    return inspect.isfunction(object) or inspect.ismethod(object)


def register(labels):
    """
    register the dict service with a labels, which will be shown in the dicts list.
    """
    def _deco(cls):
        cls.__register_label__ = _cl(labels)
        
        methods = inspect.getmembers(cls, predicate=_is_method_or_func)
        exports = []
        for method in methods:
            attrs = getattr(method[1], '__export_attrs__', None)
            if attrs and attrs[1] == -1:
                exports.append((
                    getattr(method[1], '__def_index__', 0),
                    method[1]
                ))
        exports = sorted(exports)
        for index, method in enumerate(exports):
            attrs = getattr(method[1], '__export_attrs__', None)
            attrs[1] = index

        return cls
    return _deco


def export(labels):
    """
    export dict field function with a labels, which will be shown in the fields list.
    """
    def _with(fld_func):
        @wraps(fld_func)
        def _deco(self, *args, **kwargs):
            res = fld_func(self, *args, **kwargs)
            return QueryResult(result=res) if not isinstance(res, QueryResult) else res
        _deco.__export_attrs__ = [_cl(labels), -1]
        _deco.__def_index__ = export.EXPORT_INDEX
        export.EXPORT_INDEX += 1
        return _deco
    return _with


export.EXPORT_INDEX = 0


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


_BS_LOCKS = [_threading.Lock(), _threading.Lock()]  # bs4 threading lock, overload protection


def parse_html(html):
    '''
    use bs4 lib parse HTML, run only 2 BS at the same time
    '''
    lock = _BS_LOCKS[random.randrange(0, len(_BS_LOCKS) - 1, 1)]
    lock.acquire()
    soup = BeautifulSoup(html, 'html.parser')
    lock.release()
    return soup


def service_wrap(service, *args, **kwargs):
    """
    wrap the service class constructor
    """
    def _service():
        return service(*args, **kwargs)
    return _service


class Service(object):
    '''
    Dictionary Service Abstract Class
    '''

    def __init__(self):
        self.cache = defaultdict(defaultdict)
        self._unique = self.__class__.__name__
        self._exporters = self._get_exporters()
        self._fields, self._actions = zip(*self._exporters) \
            if self._exporters else (None, None)
        self._word = ''
        # query interval: default 500ms
        self.query_interval = 0.5

    def cache_this(self, result):
        self.cache[self.word].update(result)
        return result

    def cached(self, key):
        return (self.word in self.cache) and (key in self.cache[self.word])

    def cache_result(self, key):
        return self.cache[self.word].get(key, u'')

    def _get_from_api(self):
        return {}

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_from_api().get(key, default)

    @property
    def unique(self):
        return self._unique

    @unique.setter
    def unique(self, value):
        self._unique = value

    @property
    def word(self):
        return self._word
    
    @word.setter
    def word(self, value):
        value = re.sub(r'</?\w+[^>]*>', '', value)
        self._word = value

    @property
    def quote_word(self):
        return urllib2.quote(self.word)
    
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

    def _get_exporters(self):
        flds = dict()
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method in methods:
            export_attrs = getattr(method[1], '__export_attrs__', None)
            if export_attrs:
                label, index = export_attrs[0], export_attrs[1]
                flds.update({int(index): (label, method[1])})
        sorted_flds = sorted(flds)
        return [flds[key] for key in sorted_flds]

    def active(self, fld_ord, word):
        self.word = word
        if fld_ord >= 0 and fld_ord < len(self.actions):
            return self.actions[fld_ord]()
        return QueryResult.default()

    @staticmethod
    def get_anki_label(filename, type_):
        formats = {'audio': config.sound_str,
                   'img': u'<img src="{0}">',
                   'video': u'<video controls="controls" width="100%" height="auto" src="{0}"></video>'}
        return formats[type_].format(filename)


class WebService(Service):
    """
    Web Dictionary Service
    """

    def __init__(self):
        super(WebService, self).__init__()
        self._cookie = CookieJar()
        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self._cookie))
        self.query_interval = 1.0

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    def get_response(self, url, data=None, headers=None, timeout=10):
        default_headers = {
            'User-Agent': _default_ua
        }
        if headers:
            default_headers.update(headers)

        request = urllib2.Request(url, headers=default_headers)
        try:
            response = self._opener.open(request, data=data, timeout=timeout)
            data = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)
            return data
        except Exception:
            return u''

    @classmethod
    def download(cls, url, filename, timeout=15):
        import socket
        socket.setdefaulttimeout(timeout)
        try:
            with open(filename, "wb") as f:
                f.write(requests.get(url, headers={
                    'User-Agent': _default_ua
                }).content)
            return True
        except Exception:
            pass

    class TinyDownloadError(ValueError):
        """Raises when a download is too small."""

    def net_stream(self, targets, require=None, method='GET',
                   awesome_ua=False, add_padding=False,
                   custom_quoter=None, custom_headers=None):
        """
        Returns the raw payload string from the specified target(s).
        If multiple targets are specified, their resulting payloads are
        glued together.

        Each "target" is a bare URL string or a tuple containing an
        address and a dict for what to tack onto the query string.

        Finally, a require dict may be passed to enforce a Content-Type
        using key 'mime' and/or a minimum payload size using key 'size'.
        If using multiple targets, these requirements apply to each
        response.

        The underlying library here already understands how to search
        the environment for proxy settings (e.g. HTTP_PROXY), so we do
        not need to do anything extra for that.

        If add_padding is True, then some additional null padding will
        be added onto the stream returned. This is helpful for some web
        services that sometimes return MP3s that `mplayer` clips early.
        """
        DEFAULT_TIMEOUT = 3

        PADDING = '\0' * 2**11

        assert method in ['GET', 'POST'], "method must be GET or POST"

        targets = targets if isinstance(targets, list) else [targets]
        targets = [
            (target, None) if isinstance(target, str)
            else (
                target[0],
                '&'.join(
                    '='.join([
                        key,
                        (
                            custom_quoter[key] if (custom_quoter and
                                                   key in custom_quoter)
                            else urllib2.quote
                        )(
                            val.encode('utf-8') if isinstance(val, str)
                            else str(val),
                            safe='',
                        ),
                    ])
                    for key, val in target[1].items()
                ),
            )
            for target in targets
        ]

        require = require or {}

        payloads = []

        for number, (url, params) in enumerate(targets, 1):
            desc = "web request" if len(targets) == 1 \
                else "web request (%d of %d)" % (number, len(targets))

            headers = {'User-Agent': _default_ua}
            if custom_headers:
                headers.update(custom_headers)
            
            response = urllib2.urlopen(
                urllib2.Request(
                    url=('?'.join([url, params]) if params and method == 'GET'
                         else url),
                    headers=headers,
                ),
                data=params if params and method == 'POST' else None,
                timeout=DEFAULT_TIMEOUT,
            )

            if not response:
                raise IOError("No response for %s" % desc)

            if response.getcode() != 200:
                value_error = ValueError(
                    "Got %d status for %s" %
                    (response.getcode(), desc)
                )
                try:
                    value_error.payload = response.read()
                    response.close()
                except Exception:
                    pass
                raise value_error

            if 'mime' in require and \
                    require['mime'] != format(response.info().
                                              gettype()).replace('/x-', '/'):
                value_error = ValueError(
                    "Request got %s Content-Type for %s; wanted %s" %
                    (response.info().gettype(), desc, require['mime'])
                )
                value_error.got_mime = response.info().gettype()
                value_error.wanted_mime = require['mime']
                raise value_error

            payload = response.read()
            response.close()

            if 'size' in require and len(payload) < require['size']:
                raise self.TinyDownloadError(
                    "Request got %d-byte stream for %s; wanted %d+ bytes" %
                    (len(payload), desc, require['size'])
                )

            payloads.append(payload)

        if add_padding:
            payloads.append(PADDING)
        return b''.join(payloads)

    def net_download(self, path, *args, **kwargs):
        """
        Downloads a file to the given path from the specified target(s).
        See net_stream() for information about available options.
        """
        try:
            payload = self.net_stream(*args, **kwargs)
            with open(path, 'wb') as f:
                f.write(payload)
                f.close()
            return True
        except Exception:
            return False


class _DictBuildWorker(QThread):
    """Local Dictionary Builder"""
    def __init__(self, func):
        super(_DictBuildWorker, self).__init__()
        self._builder = None
        self._func = func

    def run(self):
        try:
            self._builder = self._func()
        except Exception:
            self._builder = None

    @property
    def builder(self):
        return self._builder


class LocalService(Service):
    """
    Local Dictionary Service
    """

    def __init__(self, dict_path):
        super(LocalService, self).__init__()
        self.dict_path = dict_path
        self.builder = None
        self.missed_css = set()

    # MdxBuilder instances map
    _mdx_builders = defaultdict(dict)
    _mutex_builder = QMutex()

    @staticmethod
    def _get_builer(key, func=None):
        LocalService._mutex_builder.lock()
        key = md5(str(key).encode('utf-8')).hexdigest()
        if not(func is None):
            if not LocalService._mdx_builders[key]:
                worker = _DictBuildWorker(func)
                worker.start()
                while not worker.isFinished():
                    mw.app.processEvents()
                    worker.wait(100)
                LocalService._mdx_builders[key] = worker.builder
        LocalService._mutex_builder.unlock()
        return LocalService._mdx_builders[key]

    @property
    def support(self):
        return os.path.isfile(self.dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', u'Unkown')

    @property
    def _filename(self):
        return os.path.splitext(os.path.basename(self.dict_path))[0]

    def active(self, fld_ord, word):
        self.missed_css.clear()
        return super(LocalService, self).active(fld_ord, word)


class MdxService(LocalService):
    """
    MDX Local Dictionary Service
    """

    def __init__(self, dict_path):
        super(MdxService, self).__init__(dict_path)
        self.media_cache = defaultdict(set)
        self.cache = defaultdict(str)
        self.html_cache = defaultdict(str)
        self.query_interval = 0.01
        self.word_links = []
        self.styles = []
        if MdxService.check(self.dict_path):
            self.builder = self._get_builer(dict_path, service_wrap(MdxBuilder, dict_path))

    @staticmethod
    def check(dict_path):
        return os.path.isfile(dict_path) and dict_path.lower().endswith('.mdx')

    @property
    def support(self):
        return self.builder and MdxService.check(self.dict_path)

    @property
    def title(self):
        if config.use_filename or not self.builder._title or self.builder._title.startswith('Title'):
            return self._filename
        else:
            return self.builder._title

    @export([u'默认', u'Default'])
    def fld_whole(self):
        html = self.get_default_html()
        js = re.findall(r'<script .*?>(.*?)</script>', html, re.DOTALL)
        jsfile = re.findall(r'<script .*?src=[\'\"](.+?)[\'\"]', html, re.DOTALL)
        return QueryResult(result=html, js=u'\n'.join(js), jsfile=jsfile)

    def _get_definition_mdx(self):
        """according to the word return mdx dictionary page"""
        ignorecase = config.ignore_mdx_wordcase and (self.word != self.word.lower() or self.word != self.word.upper())
        content = self.builder.mdx_lookup(self.word, ignorecase=ignorecase)
        str_content = ""
        if len(content) > 0:
            for c in content:
                str_content += c.replace("\r\n", "").replace("entry:/", "")

        return str_content

    def _get_definition_mdd(self, word):
        """according to the keyword(param word) return the media file contents"""
        word = word.replace('/', '\\')
        ignorecase = config.ignore_mdx_wordcase and (word != word.lower() or word != word.upper())
        content = self.builder.mdd_lookup(word, ignorecase=ignorecase)
        if len(content) > 0:
            return [content[0]]
        else:
            return []

    def get_html(self):
        """get self.word's html page from MDX"""
        if not self.html_cache[self.word]:
            html = self._get_definition_mdx()
            if html:
                self.html_cache[self.word] = html
        return self.html_cache[self.word]

    def save_file(self, filepath_in_mdx, savepath):
        """according to filepath_in_mdx to get media file and save it to savepath"""
        try:
            bytes_list = self._get_definition_mdd(filepath_in_mdx)
            if bytes_list:
                if not os.path.exists(savepath):
                    with open(savepath, 'wb') as f:
                        f.write(bytes_list[0])
                return savepath
        except sqlite3.OperationalError as e:
            print(e)
            pass
        return ''

    def get_default_html(self):
        '''
        default get html from mdx interface
        '''
        if not self.cache[self.word]:
            self.word_links = [self.word.upper()]
            self._get_default_html()
        return self.cache[self.word]

    def _get_default_html(self):
        html = u''
        result = self.get_html()
        if result:
            if result.upper().find(u"@@@LINK=") > -1:
                # redirect to a new word behind the equal symol.
                word = result[len(u"@@@LINK="):].strip()
                if not word.upper() in self.word_links:
                    self.word_links.append(word.upper())
                    self.word = word
                    return self._get_default_html()
            html = self.adapt_to_anki(result)
        self.cache[self.word] = html
        return self.cache[self.word]

    def adapt_to_anki(self, html):
        """
        1. convert the media path to actual path in anki's collection media folder.
        2. remove the js codes (js inside will expires.)
        """
        # convert media path, save media files
        media_files_set = set()
        mcss = re.findall(r'href="(\S+?\.css)"', html)
        media_files_set.update(set(mcss))
        mjs = re.findall(r'src="([\w\./]\S+?\.js)"', html)
        media_files_set.update(set(mjs))
        msrc = re.findall(r'<img.*?src="([\w\./]\S+?)".*?>', html)
        media_files_set.update(set(msrc))
        msound = re.findall(r'href="sound:(.*?\.(?:mp3|wav))"', html)
        if config.export_media:
            media_files_set.update(set(msound))
        for each in media_files_set:
            html = html.replace(each, u'_' + each.split('/')[-1])
        # find sounds
        p = re.compile(
            r'<a[^>]+?href=\"(sound:_.*?\.(?:mp3|wav))\"[^>]*?>(.*?)</a>')
        html = p.sub(u"[\\1]\\2", html)
        self.save_media_files(media_files_set)
        for f in mcss:
            cssfile = u'_{}'.format(os.path.basename(f.replace('\\', os.path.sep)))
            # if not exists the css file, the user can place the file to media
            # folder first, and it will also execute the wrap process to generate
            # the desired file.
            if not os.path.exists(cssfile):
                css_src = self.dict_path.replace(self._filename + u'.mdx', f)
                if os.path.exists(css_src):
                    shutil.copy(css_src, cssfile)
                else:    
                    self.missed_css.add(cssfile[1:])
            new_css_file, wrap_class_name = wrap_css(cssfile)
            html = html.replace(cssfile, new_css_file)
            # add global div to the result html
            html = u'<div class="{0}">{1}</div>'.format(
                wrap_class_name, html)

        return html

    def save_default_file(self, filepath_in_mdx, savepath=None):
        '''
        default save file interface
        '''
        basename = os.path.basename(filepath_in_mdx.replace('\\', os.path.sep))
        if savepath is None:
            savepath = '_' + basename
        if os.path.exists(savepath):
            return savepath
        try:
            src_fn = self.dict_path.replace(self._filename + u'.mdx', basename)
            if os.path.exists(src_fn):
                shutil.copy(src_fn, savepath)
                return savepath
            else:
                ignorecase = config.ignore_mdx_wordcase and (filepath_in_mdx != filepath_in_mdx.lower() or filepath_in_mdx != filepath_in_mdx.upper())
                bytes_list = self.builder.mdd_lookup(filepath_in_mdx, ignorecase=ignorecase)
                if bytes_list:
                    with open(savepath, 'wb') as f:
                        f.write(bytes_list[0])
                    return savepath
        except sqlite3.OperationalError as e:
            print('save default file error', e)
            pass

    def save_media_files(self, data):
        """
        get the necessary static files from local mdx dictionary
        ** kwargs: data = list
        """
        diff = data.difference(self.media_cache['files'])
        self.media_cache['files'].update(diff)
        lst, errors = list(), list()
        wild = [
            '*' + os.path.basename(each.replace('\\', os.path.sep)) for each in diff]
        try:
            for each in wild:
                keys = self.builder.get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                    lst.append(each[1:])
                else:
                    lst.extend(keys)
            for each in lst:
                self.save_default_file(each)
        except AttributeError:
            pass

        return errors


class StardictService(LocalService):
    '''
    Stardict Local Dictionary Service
    '''
    def __init__(self, dict_path):
        super(StardictService, self).__init__(dict_path)
        self.query_interval = 0.05
        if StardictService.check(self.dict_path):
            dict_path = dict_path[:-4]
            self.builder = self._get_builer(
                dict_path,
                service_wrap(StardictBuilder, dict_path, in_memory=False)
            )
            # if self.builder:
            #    self.builder.get_header()

    @staticmethod
    def check(dict_path):
        return os.path.isfile(dict_path) and dict_path.lower().endswith('.ifo')

    @property
    def support(self):
        return self.builder and StardictService.check(self.dict_path)

    @property
    def title(self):
        if config.use_filename or not self.builder.ifo.bookname:
            return self._filename
        else:
            return self.builder.ifo.bookname

    @export([u'默认', u'Default'])
    def fld_whole(self):
        # self.builder.check_build()
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
        if self['result'] is None:
            self['result'] = ""

    def set_styles(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value

    @classmethod
    def default(cls):
        return QueryResult(result="")
