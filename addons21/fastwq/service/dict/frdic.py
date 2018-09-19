#-*- coding:utf-8 -*-
import base64
import re
import urllib.request as urllib2
import os
from ..base import *


css = ''

@register([u'法语助手', u'frdic'])
class Frdic(WebService):

    def __init__(self):
        super(Frdic, self).__init__()

    def _get_from_api(self):
        url = 'http://www.frdic.com/dicts/fr/{}'.format(self.quote_word)
        try:
            result = {}
            html = self.get_response(url, timeout=5)
            soup = parse_html(html)

            def _get_from_element(dict, key, soup, tag, id=None, class_=None):
                baseURL = 'http://www.frdic.com/'
                # element = soup.find(tag, id=id, class_=class_)  # bs4
                if id:
                    element = soup.find(tag, {"id": id})
                if class_:
                    element = soup.find(tag, {"class": class_})
                if element:
                    dict[key] = str(element)
                    dict[key] = re.sub(
                        r'href="/', 'href="' + baseURL, dict[key])
                    dict[key] = re.sub(r'声明：.*。', '', dict[key])
                    dict[key] = dict[key]
                return dict

            # '<span class="Phonitic">[bɔ̃ʒur]</span>'
            result = _get_from_element(
                result, 'phonitic', soup, 'span', class_='Phonitic')
            # '<div id='FCChild'  class='expDiv'>'
            result = _get_from_element(
                result, 'fccf', soup, 'div', id='ExpFCChild')  # 法汉-汉法词典
            result = _get_from_element(
                result, 'example', soup, 'div', id='TingLijuChild')  # 法语例句库
            result = _get_from_element(
                result, 'syn', soup, 'div', id='SYNChild')  # 近义、反义、派生词典
            result = _get_from_element(
                result, 'ff', soup, 'div', id='FFChild')  # 法法词典
            result = _get_from_element(
                result, 'fe', soup, 'div', id='FEChild')  # 法英词典

            return self.cache_this(result)
        except Exception as e:
            return {}

    @export([u'真人发音', u'Real person pronunciation'])
    def fld_sound(self):
        url = 'https://api.frdic.com/api/v2/speech/speakweb?langid=fr&txt=QYN{word}'.format(
            word=urllib2.quote(base64.b64encode(self.word.encode('utf-8')))
        )
        filename = get_hex_name(self.unique.lower(), url, 'mp3')
        if os.path.exists(filename) or self.net_download(filename, url):
                return self.get_anki_label(filename, 'audio')
        return ''
    @export('PHON')
    def fld_phonetic(self):
        return self._get_field('phonitic')

    @export([u'法汉-汉法词典', u'French-chinese/chinese-french dictionary'])
    def fld_fccf(self):
        return self._get_field('fccf')

    @export([u'法语例句库', u'French examples'])
    @with_styles(css=css)
    def fld_example(self):
        return self._get_field('example')

    @export([u'近义、反义、派生词典', u'Synonyms, antonyms, derivatives'])
    @with_styles(css=css)
    def fld_syn(self):
        return self._get_field('syn')

    @export([u'法法词典', u'French-french dictionary'])
    @with_styles(css=css)
    def fld_ff(self):
        return self._get_field('ff')

    @export([u'法英词典', u'French-english dictionary'])
    @with_styles(css=css)
    def fld_fe(self):
        return self._get_field('fe')
