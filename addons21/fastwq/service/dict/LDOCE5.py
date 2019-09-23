#-*- coding:utf-8 -*-
import os
import re
import random
from ..base import *
# from BeautifulSoup import BeautifulSoup
# from bs4 import BeautifulSoup


VOICE_PATTERN = r'href="sound:\/\/([\w\/]+%s\/\w*\.mp3)"'
VOICE_PATTERN_WQ = r'<span class="%s"><a href="sound://([\w/]+\w*\.mp3)">(.*?)</span %s>'
MAPPINGS = [
    ['br', [re.compile(VOICE_PATTERN % r'breProns')]],
    ['us', [re.compile(VOICE_PATTERN % r'ameProns')]]
]
LANG_TO_REGEXPS = {lang: regexps for lang, regexps in MAPPINGS}
DICT_PATH = u'/Users/brian/Documents/LDOCE5++ V 2-15/LDOCE5++ V 2-15.mdx' # u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'


@register([u'本地词典-LDOCE5++', u'MDX-LDOCE5++'])
class Ldoce5plus(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'LDOCE5++'):
                    dict_path = service.dict_path
                    break
        super(Ldoce5plus, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    def _fld_voice(self, html, voice):
        """获取发音字段"""
        for regexp in LANG_TO_REGEXPS[voice]:
            match = regexp.search(html)
            if match:
                val = '/' + match.group(1)
                name = get_hex_name('mdx-'+self.unique.lower(), val, 'mp3')
                name = self.save_file(val, name)
                if name:
                    return self.get_anki_label(name, 'audio')
        return ''

    @export('BRE_PRON')
    def fld_voicebre(self):
        return self._fld_voice(self.get_html(), 'br')

    @export('AME_PRON')
    def fld_voiceame(self):
        return self._fld_voice(self.get_html(), 'us')

    @export('All examples with audios')
    def fld_sentence_audio(self):
        return self._range_sentence_audio([i for i in range(0, 100)])

    @export('Random example with audio')
    def fld_random_sentence_audio(self):
        return self._range_sentence_audio()

    @export('First example with audio')
    def fld_first1_sentence_audio(self):
        return self._range_sentence_audio([0])

    @export('First 2 examples with audios')
    def fld_first2_sentence_audio(self):
        return self._range_sentence_audio([0, 1])

    def _fld_audio(self, audio):
        name = get_hex_name('mdx-'+self.unique.lower(), audio, 'mp3')
        name = self.save_file(audio, name)
        if name:
            return self.get_anki_label(name, 'audio')
        return ''

    def _range_sentence_audio(self, range_arr=None):
        m = re.findall(r'<div class="EXAMPLE">\s*.*>\s*.*<\/div>', self.get_html())
        if m:
            soup = parse_html(m[0])
            el_list = soup.findAll('div', {'class':'EXAMPLE'})
            if el_list:
                maps = []
                for element in el_list:
                    i_str = ''
                    for content in element.contents:
                        i_str = i_str + str(content)
                    sound = re.search(r'<a[^>]+?href=\"sound\:\/(.*?\.mp3)\".*<\/a>', i_str)
                    if sound:
                        maps.append([sound, i_str])
            my_str = ''
            range_arr = range_arr if range_arr else [random.randrange(0, len(maps) - 1, 1)]
            for i, e in enumerate(maps):
                if i in range_arr:
                    i_str = e[1]
                    sound = e[0]
                    mp3 = self._fld_audio(sound.groups()[0])
                    i_str = re.sub('<[^<]+?>', '', i_str)
                    i_str = re.sub('\xa0', '', i_str)
                    # i_str = re.sub(r'<a[^>]+?href=\"sound\:\/.*?\.mp3\".*<\/a>', '', i_str).strip()
                    # chinese text
                    # cn_text = re.search(r'<div class="cn_txt">(\s*\S*)<\/div><\/span>', i_str)
                    # cn_text_strip = " "
                    # if cn_text:
                    #     cn_text_strip = cn_text.groups()[0]
                    # i_str = re.sub(r'(<div class="cn_txt">\s*\S*<\/div>)<\/span>', '', i_str).strip()
                    # my_str = my_str + mp3 + ' ' + i_str  + cn_text_strip + '<br>'
                    my_str = my_str + mp3 + ' ' + i_str  + '<br>'
            return my_str
        return ''
