#-*- coding:utf-8 -*-

import os
from bs4 import BeautifulSoup
import requests
from ..base import *
from ...utils.misc import format_multi_query_word

@register('Span¡shD!ct')
class SpanishDict(WebService):

    def _get_from_api(self):
        url = 'https://www.spanishdict.com/translate/{}'.format(format_multi_query_word(self.quote_word))
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        # Top Container
        word_info = {}

        word_info['image_url'] = soup.find_all('img')[1]['src']
        word_info['test'] = str(soup.find_all('img'))
        return self.cache_this(word_info)
        
    @export([u'图片', u'Image'])
    def fld_image(self):
        #image_url = "https://d25rq8gxcq0p71.cloudfront.net/dictionary-images/300/c5453acf-e0f1-4fe4-9534-607c9aa21e85.jpg"
        image_url = self._get_field('image_url')
        file_extension = os.path.splitext(image_url)[1][1:].strip().lower()
        filename = get_hex_name(self.unique.lower(), image_url, file_extension)
        if os.path.exists(filename) or self.download(image_url, filename):
            return self.get_anki_label(filename, 'img')
        return ''
        
    @export([u'测试链接', u'test'])
    def fld_tst(self):
        return self._get_field('test')
