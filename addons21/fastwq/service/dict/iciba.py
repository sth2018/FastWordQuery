#-*- coding:utf-8 -*-
import os
import re
import json
from collections import defaultdict
from aqt.utils import showInfo, showText

from ..base import *
from ...utils import ignore_exception

iciba_download_mp3 = True


@register([u'爱词霸', u'iciba'])
class ICIBA(WebService):

    def __init__(self):
        super(ICIBA, self).__init__()

    def _get_from_api(self):
        resp = defaultdict(str)
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01'}
        # try:
        html = self.get_response(
            'http://www.iciba.com/index.php?a=getWordMean&c=search&word=' + self.quote_word, 
            headers=headers,
            timeout=5
        )
        resp = json.loads(html)
        # self.cache_this(resp['baesInfo']['symbols'][0])
        # self.cache_this(resp['sentence'])
        # showText(str(self.cache[self.word]))
        # return self.cache[self.word]
        return self.cache_this(resp)
        # except Exception as e:
        #     return resp

    @ignore_exception
    @export('AME_PHON')
    def fld_phonetic_us(self):
        seg = self._get_field('baesInfo')
        return '/' + seg['symbols'][0]['ph_am'] + '/'

    @ignore_exception
    @export('BRE_PHON')
    def fld_phonetic_uk(self):
        seg = self._get_field('baesInfo')
        return '/' + seg['symbols'][0]['ph_en'] + '/'

    @ignore_exception
    @export('AME_PRON')
    def fld_mp3_us(self):
        seg = self._get_field('baesInfo')
        audio_url, t = seg['symbols'][0]['ph_am_mp3'], 'am'
        if not audio_url:
            audio_url, t = seg['symbols'][0]['ph_tts_mp3'], 'tts'
        if iciba_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @ignore_exception
    @export('BRE_PRON')
    def fld_mp3_uk(self):
        seg = self._get_field('baesInfo')
        audio_url, t = seg['symbols'][0]['ph_en_mp3'], 'en'
        if not audio_url:
            audio_url, t = seg['symbols'][0]['ph_tts_mp3'], 'tts'
        if iciba_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @ignore_exception
    @export([u'释义', u'Basic definition'])
    def fld_definition(self):
        seg = self._get_field('baesInfo')
        parts = seg['symbols'][0]['parts']
        return u'<br>'.join([part['part'] + ' ' + '; '.join(part['means']) for part in parts])

    @ignore_exception
    @export([u'双语例句', u'Bilingual examples'])
    def fld_samples(self):
        sentences = ''
        segs = self._get_field('sentence')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>
                        <div class="sen_en">{0}</div>
                        <div class="sen_cn">{1}</div>
                    </li>""".format(seg['Network_en'], seg['Network_cn'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export([u'权威例句', u'Authoritative examples'])
    def fld_auth_sentence(self):
        sentences = ''
        segs = self._get_field('auth_sentence')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>{0}  [{1}]</li>""".format(
                    seg['res_content'], seg['source'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export([u'句式用法', u'Sentence pattern usage'])
    def fld_usage(self):
        sentences = ''
        segs = self._get_field('jushi')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>
                        <div class="sen_en">{0}</div>
                        <div class="sen_cn">{1}</div>
                    </li>""".format(seg['english'], seg['chinese'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export([u'使用频率', u'Frequency rate'])
    def fld_frequence(self):
        seg = self._get_field('baesInfo')
        return str(seg['frequence'])

    @ignore_exception
    @export([u'英文例句', u'English example'])
    def fld_st(self):
        sentences = ''
        segs = self._get_field('sentence')
        for i, seg in enumerate(segs):
            sentences = u"""{}""".format(seg['Network_en'])
            break
        return sentences
    
    @ignore_exception
    @export([u'例句翻译', u'Examples'])
    def fld_sttr(self):
        sentences = ''
        segs = self._get_field('sentence')
        for i, seg in enumerate(segs):
            sentences = u"""{}""".format(seg['Network_cn'])
            break
        
        return sentences
