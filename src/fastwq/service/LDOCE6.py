#-*- coding:utf-8 -*-
import re
from .base import MdxService, export, register, with_styles, parseHtml

PATH = u'D:\\mdx_server\\mdx\\LDOCE6.mdx'

VOICE_PATTERN = r'<a href="sound://([\w/]+\w*\.mp3)"><img src="img/spkr_%s.png"></a>'
MAPPINGS = [
    ['br', [re.compile(VOICE_PATTERN % r'r')]],
    ['us', [re.compile(VOICE_PATTERN % r'b')]]
]
LANG_TO_REGEXPS = {lang: regexps for lang, regexps in MAPPINGS}


@register([u'本地词典-LDOCE6', u'MDX-LDOCE6'])
class Ldoce6(MdxService):

    def __init__(self):
        super(Ldoce6, self).__init__(PATH)

    @property
    def unique(self):
        return self.__class__.__name__

    @property
    def title(self):
        return self.__register_label__

    @export('PHON', 1)
    def fld_phonetic(self):
        html = self.get_html()
        m = re.search(r'<span class="pron">(.*?)</span>', html)
        if m:
            return m.groups()[0]
        return ''

    def _fld_voice(self, html, voice):
        """获取发音字段"""
        from hashlib import sha1
        for regexp in LANG_TO_REGEXPS[voice]:
            match = regexp.search(html)
            if match:
                val = '/' + match.group(1)
                hex_digest = sha1(
                    val.encode('utf-8') if isinstance(val, unicode)
                    else val
                ).hexdigest().lower()

                assert len(hex_digest) == 40, "unexpected output from hash library"
                name = '.'.join([
                        '-'.join([
                            'mdx', self.unique.lower(), hex_digest[:8], hex_digest[8:16],
                            hex_digest[16:24], hex_digest[24:32], hex_digest[32:],
                        ]),
                        'mp3',
                    ])
                name = self.save_file(val, name)
                if name:
                    return self.get_anki_label(name, 'audio')
        return ''

    @export('BRE_PRON', 2)
    def fld_voicebre(self):
        return self._fld_voice(self.get_html(), 'br')

    @export('AME_PRON', 3)
    def fld_voiceame(self):
        return self._fld_voice(self.get_html(), 'us')

    @export('EXAMPLE', 4)
    def fld_sentence(self):
        m = re.findall(r'<span class="example"\s*.*>\s*.*<\/span>', self.get_html())
        if m:
            soup = parseHtml(m[0])
            el_list = soup.findAll('span', {'class':'example'})
            if el_list:
                maps = [u''.join(str(content).decode('utf-8') for content in element.contents) 
                                    for element in el_list]
            my_str = ''
            for i_str in maps:
                i_str = re.sub(r'<a[^>]+?href=\"sound\:.*\.mp3\".*</a>', '', i_str)
                i_str = i_str.replace('&nbsp;', '')
                my_str = my_str + '<li>' + i_str + '</li>'
            return self._css(my_str)
        return ''

    @export('DEF', 5)
    def fld_definate(self):
        m = m = re.findall(r'<span class="def"\s*.*>\s*.*<\/span>', self.get_html())
        if m:
            soup = parseHtml(m[0])
            el_list = soup.findAll('span', {'class':'def'})
            if el_list:
                maps = [u''.join(str(content).decode('utf-8') for content in element.contents) 
                                    for element in el_list]
            my_str = ''
            for i_str in maps:
                my_str = my_str + '<li>' + i_str + '</li>'
            return self._css(my_str)
        return ''

    @with_styles(cssfile='_ldoce6.css')
    def _css(self, val):
        return val
    