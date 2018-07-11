#-*- coding:utf-8 -*-
import json
import re
from .base import WebService, export, register, with_styles

bing_download_mp3 = True

@register([u'Bing xtk', u'Bing xtk'])
class BingXtk(WebService):

    def __init__(self):
        super(BingXtk, self).__init__()

    def _get_content(self):
        result = {
            'pronunciation': {'AmE': '', 'BrE': '', 'AmEmp3': '', 'BrEmp3': ''},
            'def': '',
            'sams': '',
        }
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'WordQuery Addon (Anki)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        word = self.word.replace(' ', '_').encode('utf-8')
        url = u'http://xtk.azurewebsites.net/BingDictService.aspx?Word={}'.format(word)
        try:
            result.update(json.loads(self.get_response(url, headers=headers, timeout=10)))
            return self.cache_this(result)
        except:
            return result

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @export('AME_PHON', 1)
    def fld_phonetic_us(self):
        seg = self._get_field('pronunciation')
        return seg.get('AmE', u'')

    @export('BRE_PHON', 2)
    def fld_phonetic_uk(self):
        seg = self._get_field('pronunciation')
        return seg.get('BrE', u'')

    def _fld_mp3(self, fld):
        audio_url = self._get_field('pronunciation')[fld]
        if bing_download_mp3 and audio_url:
            filename = u'bing_' + u''.join(re.findall(r'\w*\.mp3', audio_url))
            if filename and self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('AME_PRON', 3)
    def fld_mp3_us(self):
        return self._fld_mp3('AmEmp3')

    @export('BRE_PRON', 4)
    def fld_mp3_uk(self):
        return self._fld_mp3('BrEmp3')
    
    @with_styles(css='.pos{font-weight:bold;margin-right:4px;}', need_wrap_css=True, wrap_class='bing')
    def _css(self, val):
        return val

    @export('DEF', 5)
    def fld_definition(self):
        segs = self._get_field('defs')
        if isinstance(segs, list) and len(segs) > 0:
            val = u'<br>'.join([u'''<span class="pos"><b>{0}</b></span>
                                    <span class="def">{1}</span>'''.format(seg['pos'], seg['def']) for seg in segs])
            return self._css(val)
        return ''
    
    @export('EXAMPLE', 6)
    def fld_samples(self):
        max_numbers = 10
        segs = self._get_field('sams')
        sentences = ''
        for i, seg in enumerate(segs):
            sentences += u"""<li><div class="se_li1">
                            <div class="sen_en">{0}</div>
                            <div class="sen_cn">{1}</div>
                        </div></li>""".format(seg['eng'], seg['chn'])
            if i == 9:
                break
        if sentences:
            return u"""<div class="se_div">
                            <div class="sentenceCon">
                                <div id="sentenceSeg"><ol>{0}</ol></div>
                            </div>
                    </div>""".format(sentences)
        return ''
