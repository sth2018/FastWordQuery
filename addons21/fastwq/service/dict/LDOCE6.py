#-*- coding:utf-8 -*-
import os
import re
from ..base import *


VOICE_PATTERN = r'<a href="sound://([\w/]+\w*\.mp3)"><img src="img/spkr_%s.png"></a>'
VOICE_PATTERN_WQ = r'<span class="%s"><a href="sound://([\w/]+\w*\.mp3)">(.*?)</span %s>'
MAPPINGS = [
    ['br', [re.compile(VOICE_PATTERN % r'r'), re.compile(VOICE_PATTERN_WQ % (r'brevoice', r'brevoice'))]],
    ['us', [re.compile(VOICE_PATTERN % r'b'), re.compile(VOICE_PATTERN_WQ % (r'amevoice', r'amevoice'))]]
]
LANG_TO_REGEXPS = {lang: regexps for lang, regexps in MAPPINGS}
DICT_PATH = u'' # u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'


@register([u'本地词典-LDOCE6', u'MDX-LDOCE6'])
class Ldoce6(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'LDOCE6'):
                    dict_path = service.dict_path
                    break
        super(Ldoce6, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    @export('PHON')
    def fld_phonetic(self):
        html = self.get_html()
        m = re.search(r'<span class="pron">(.*?)</span>', html)
        if m:
            return m.groups()[0]
        return ''

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

    def _fld_image(self, img):
        val = '/' + img
        # file extension isn't always jpg
        file_extension = os.path.splitext(img)[1][1:].strip().lower()
        name = get_hex_name('mdx-'+self.unique.lower(), val, file_extension)
        name = self.save_file(val, name)
        if name:
            return self.get_anki_label(name, 'img')
        return ''

    @export('IMAGE')
    def fld_image(self):
        html = self.get_html()
        m = re.search(r'<span class="imgholder"><img src="(.*?)".*?></span>', html)
        if m:
            return self._fld_image(m.groups()[0])
        return ''

    @export('EXAMPLE')
    def fld_sentence(self):
        m = re.findall(r'<span class="example"\s*.*>\s*.*<\/span>', self.get_html())
        if m:
            soup = parse_html(m[0])
            el_list = soup.findAll('span', {'class':'example'})
            if el_list:
                maps = [u''.join(str(content) for content in element.contents) 
                                    for element in el_list]
            my_str = ''
            for i_str in maps:
                i_str = re.sub(r'<a[^>]+?href=\"sound\:.*\.mp3\".*</a>', '', i_str).strip()
                my_str = my_str + '<li>' + i_str + '</li>'
            return self._css(my_str)
        return ''

    def _fld_audio(self, audio):
        name = get_hex_name('mdx-'+self.unique.lower(), audio, 'mp3')
        name = self.save_file(audio, name)
        if name:
            return self.get_anki_label(name, 'audio')
        return ''

    @export(u'Examples with audios')
    def fld_sentence_audio(self):
        m = re.findall(r'<span class="example"\s*.*>\s*.*<\/span>', self.get_html())
        if m:
            soup = parse_html(m[0])
            el_list = soup.findAll('span', {'class':'example'})
            if el_list:
                maps = [u''.join(str(content) for content in element.contents) 
                                    for element in el_list]
            my_str = ''
            for i_str in maps:
                sound = re.search(r'<a[^>]+?href=\"sound\:\/(.*?\.mp3)\".*</a>', i_str)
                if sound:
                    mp3 = self._fld_audio(sound.groups()[0])
                    i_str = re.sub(r'<a[^>]+?href=\"sound\:.*\.mp3\".*</a>', '', i_str).strip()
                    my_str = my_str + '<li>' + i_str + ' ' + mp3 + '</li>'
            return self._css(my_str)
        return ''

    @export('DEF')
    def fld_definate(self):
        m = m = re.findall(r'<span class="def"\s*.*>\s*.*<\/span>', self.get_html())
        if m:
            soup = parse_html(m[0])
            el_list = soup.findAll('span', {'class':'def'})
            if el_list:
                maps = [u''.join(str(content) for content in element.contents) 
                                    for element in el_list]
            my_str = ''
            for i_str in maps:
                my_str = my_str + '<li>' + i_str + '</li>'
            return self._css(my_str)
        return ''

    @with_styles(cssfile='_ldoce6.css')
    def _css(self, val):
        return val
    