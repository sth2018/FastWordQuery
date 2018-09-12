#-*- coding:utf-8 -*-
import re
import os
from ..base import *

dreye_download_mp3 = True

@register([u'译典通', u'Dr.eye'])
class Dreye(WebService):

    def __init__(self):
        super(Dreye, self).__init__()

    def _get_from_api(self):
        data = self.get_response(u"https://yun.dreye.com/dict_new/dict.php?w={}&hidden_codepage=01".format(self.quote_word))
        soup = parse_html(data)
        result = {
            'phon': '',
            'pron': '',
            'pos': '',
            'def': ''
        }

        #音标
        element = soup.find('span', class_='phonetic')
        if element:
            result['phon'] = element.get_text()

        # 发音
        mp3_regexp = re.compile(r'var *RealSoundPath += +"(.*)";')
        mp3_match = mp3_regexp.search(data.decode('utf-8'))
        if mp3_match:
            result['pron'] = u'{}'.format(mp3_match.group(1))
        #动变
        element = soup.find('div', id='digest')
        if element:
            result['pos'] = u'{}'.format(str(element))
        #释义
        element = soup.find('div', id='usual')
        if element:
            result['def'] = u'{}'.format(str(element))

        return self.cache_this(result)

    @with_styles(need_wrap_css=True, cssfile='_dreye.css')
    def _css(self, val):
        return val

    @export('PHON')
    def fld_phonetic_us(self):
        return self._get_field('phon')

    @export('PRON')
    def fld_mp3(self):
        audio_url = self._get_field('pron')
        if dreye_download_mp3 and audio_url:
            filename = get_hex_name('dreye', audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export([u'摘要', u'Digest'])
    def fld_pos(self):
        val = self._get_field('pos')
        if val == None or val == '':
            return ''
        return self._css(val)
    
    @export('DEF')
    def fld_definition(self):
        val = self._get_field('def')
        if val == None or val == '':
            return ''
        return self._css(val)
