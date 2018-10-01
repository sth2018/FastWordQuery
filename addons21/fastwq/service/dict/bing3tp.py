#-*- coding:utf-8 -*-
import json
import re
import os
from ..base import *

bing_download_mp3 = True

@register([u'Bing xtk', u'Bing xtk'])
class BingXtk(WebService):

    def __init__(self):
        super(BingXtk, self).__init__()

    def _get_from_api(self):
        result = {
            'pronunciation': {'AmE': '', 'BrE': '', 'AmEmp3': '', 'BrEmp3': ''},
            'def': [],
            'sams': [],
        }
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'WordQuery Addon (Anki)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        url = u'http://xtk.azurewebsites.net/BingDictService.aspx?Word={}'.format(self.quote_word)
        try:
            result.update(json.loads(self.get_response(url, headers=headers, timeout=10)))
        except:
            pass
        return self.cache_this(result)

    @export('AME_PHON')
    def fld_phonetic_us(self):
        seg = self._get_field('pronunciation')
        phon = seg.get('AmE', u'') if seg else u''
        if phon and phon[0:1] not in '/[':
            return u'/{}/'.format(phon)
        return u''

    @export('BRE_PHON')
    def fld_phonetic_uk(self):
        seg = self._get_field('pronunciation')
        phon = seg.get('BrE', u'') if seg else u''
        if phon and phon[0:1] not in '/[':
            return u'/{}/'.format(phon)
        return u''

    def _fld_mp3(self, fld):
        seg = self._get_field('pronunciation')
        audio_url = seg[fld] if seg else u''
        if bing_download_mp3 and audio_url:
            filename = get_hex_name('bing', audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('AME_PRON')
    def fld_mp3_us(self):
        return self._fld_mp3('AmEmp3')

    @export('BRE_PRON')
    def fld_mp3_uk(self):
        return self._fld_mp3('BrEmp3')
    
    @with_styles(css='.pos{font-weight:bold;margin-right:4px;}', need_wrap_css=True, wrap_class='bing')
    def _css(self, val):
        return val

    @export('DEF')
    def fld_definition(self):
        segs = self._get_field('defs')
        if isinstance(segs, list) and len(segs) > 0:
            val = u'<br>'.join([u'''<span class="pos"><b>{0}</b></span>
                                    <span class="def">{1}</span>'''.format(seg['pos'], seg['def']) for seg in segs])
            return self._css(val)
        return ''
    
    @export('EXAMPLE')
    def fld_samples(self):
        max_numbers = 10
        segs = self._get_field('sams')
        if segs:
            sentences = u''
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
        return u''
