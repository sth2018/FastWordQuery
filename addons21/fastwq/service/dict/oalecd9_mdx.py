#-*- coding:utf-8 -*-
import os
import re
import random
from ..base import *
# from BeautifulSoup import BeautifulSoup
# from bs4 import BeautifulSoup


VOICE_PATTERN = r'<a href="sound:\/\/([\w\/]*\w*\.mp3)"><audio-%s>'
VOICE_PATTERN_WQ = r'<span class="%s"><a href="sound://([\w/]+\w*\.mp3)">(.*?)</span %s>'
MAPPINGS = [
    ['br', [re.compile(VOICE_PATTERN % r'gb')]],
    ['us', [re.compile(VOICE_PATTERN % r'us')]]
]
LANG_TO_REGEXPS = {lang: regexps for lang, regexps in MAPPINGS}
DICT_PATH = u"/Users/brian/Documents/牛津高阶英汉双解词典第9例句发音版_V1.0.3c/牛津高阶英汉双解词典(第9版)_V1.0.3c.mdx" # u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'


@register([u'本地词典-牛津高阶9例句发音', u'牛津高阶9例句发音'])
class oalecd9_mdx(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'牛津高阶英汉双解词典'):
                    dict_path = service.dict_path
                    break
        super(oalecd9_mdx, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    def _fld_voice(self, html, voice):
        """获取发音字段"""
        for regexp in LANG_TO_REGEXPS[voice]:
            original_word = self.word
            if html.startswith('@@@LINK='):
                self.word = html[8:]
                html = self.get_html()
            match = regexp.findall(html)
            if match:
                selected_voice = match[0]
                for voice in match:
                    if original_word in voice:
                        selected_voice = voice
                        break
                self.word = original_word
                val = '/' + selected_voice
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
        m = self.get_html()
        if m:
            soup = parse_html(m)
            el_list = soup.findAll('x-g-blk', )
            if el_list:
                maps = []
                for element in el_list:
                    sounds = element.find_all('a')
                    if sounds:
                        br_sound = 'None'
                        us_sound = None
                        en_text = cn_text = ''
                        for sound in sounds:
                            if sound.find(['audio-gbs-liju','audio-brs-liju']):
                                br_sound = sound['href'][7:]
                            elif sound.find(['audio-uss-liju','audio-ams-liju']):
                                us_sound = sound['href'][7:]
                        try:
                            en_text = element.x['wd']
                            cn_text = element.x.chn.contents[1]
                        except:
                            continue
                        if us_sound: # I mainly use us_sound
                            maps.append([br_sound, us_sound,en_text,cn_text])

            my_str = ''
            range_arr = range_arr if range_arr else [random.randrange(0, len(maps) - 1, 1)]
            if maps:
                for i, e in enumerate(maps):
                    if i in range_arr:
                        br_sound = e[0]
                        us_sound = e[1]
                        en_text = e[2]
                        cn_text = e[3]
                        us_mp3 = self._fld_audio(us_sound)
                        if br_sound != 'None':
                            br_mp3 = self._fld_audio(br_sound)
                        else:
                            br_mp3 = ''
                        # please modify the code here to get br_mp3
                        # my_str = my_str + br_mp3 + ' ' + en_text  + cn_text + '<br>'
                        # my_str = my_str + us_mp3 + en_text  + cn_text + '<br>'
                        my_str = my_str + br_mp3 + us_mp3 + en_text  + cn_text + '<br>'
            return my_str
        return ''
