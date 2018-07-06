#-*- coding:utf-8 -*-
import re

from aqt.utils import showInfo, showText
from .base import WebService, export, register, with_styles, parseHtml


@register([u'必应', u'Bing'])
class Bing(WebService):

    def __init__(self):
        super(Bing, self).__init__()

    def _get_content(self):
        word = self.word.replace(' ', '_')
        data = self.get_response(u"http://cn.bing.com/dict/search?q={}&mkt=zh-cn".format(word))
        soup = parseHtml(data)
        result = {}

        element = soup.find('div', class_='hd_prUS')
        if element:
            result['phonitic_us'] = str(element).decode('utf-8')

        element = soup.find('div', class_='hd_pr')
        if element:
            result['phonitic_uk'] = str(element).decode('utf-8')

        element = soup.find('div', class_='hd_if')
        if element:
            result['participle'] = str(element).decode('utf-8')

        element = soup.find('div', class_='qdef')
        if element:
            element = getattr(element, 'ul', '')
            if element:
                result['def'] = u''.join([str(content) for content in element.contents])

        return self.cache_this(result)

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @export('AME_PHON', 1)
    def fld_phonetic_us(self):
        return self._get_field('phonitic_us')

    @export('BRE_PHON', 2)
    def fld_phonetic_uk(self):
        return self._get_field('phonitic_uk')

    @export([u'词语时态', u'Participle'], 3)
    def fld_participle(self):
        return self._get_field('participle')

    @with_styles(css='.pos{font-weight:bold;margin-right:4px;}', need_wrap_css=True, wrap_class='bing')
    def _css(self, val):
        return val
    
    @export('DEF', 4)
    def fld_definition(self):
        val = self._get_field('def')
        if val == None or val == '':
            return ''
        return self._css(val)
