#-*- coding:utf-8 -*-
import json
import os
from collections import defaultdict
from ..base import *


@register([u'百词斩', u'Baicizhan'])
class Baicizhan(WebService):

    bcz_download_mp3 = True
    bcz_download_img = True

    def __init__(self):
        super(Baicizhan, self).__init__()

    def _get_from_api(self):
        url = u"http://mall.baicizhan.com/ws/search?w={}".format(self.quote_word)
        result = {
            "accent": u"",
            "img": u"",
            "mean_cn": u"",
            "st": u"",
            "sttr": u"",
            "tv": u"",
            "word": u"",
            "df": u'',
        }
        try:
            html = self.get_response(url, timeout=5)#urllib2.urlopen(url, timeout=5).read()
            result.update(json.loads(html))
        except:
            pass
        return self.cache_this(result)

    @export('PRON')
    def fld_phonetic(self):
        url = u'http://baicizhan.qiniucdn.com/word_audios/{}.mp3'.format(self.quote_word)
        audio_name = get_hex_name(self.unique.lower(), url, 'mp3')
        if self.bcz_download_mp3:
            if os.path.exists(audio_name) or self.download(url, audio_name, 5):
                with open(audio_name, 'rb') as f:
                    if f.read().strip() == '{"error":"Document not found"}':
                        res = ''
                    else:
                        res = self.get_anki_label(audio_name, 'audio')
                if not res:
                    os.remove(audio_name)
            else:
                res = ''
            return res
        else:
            return url

    @export('PHON')
    def fld_phon(self):
        return self._get_field('accent')

    @export('IMAGE')
    def fld_img(self):
        url = self._get_field('img')
        if url and self.bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if os.path.exists(filename) or self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        #return self.get_anki_label(url, 'img')
        return ''

    @export([u'象形', u'Pictogram'])
    def fld_df(self):
        url = self._get_field('df')
        if url and self.bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if os.path.exists(filename) or self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        #return self.get_anki_label(url, 'img')
        return ''

    @export(u'DEF')
    def fld_mean(self):
        return self._get_field('mean_cn')

    @export(u'EXAMPLE')
    def fld_st(self):
        return self._get_field('st')

    @export('TRANS')
    def fld_sttr(self):
        return self._get_field('sttr')

    @export([u'单词tv', u'TV'])
    def fld_tv_url(self):
        video = self._get_field('tv')
        if video:
            return self.get_anki_label(video, 'video')
        return ''
