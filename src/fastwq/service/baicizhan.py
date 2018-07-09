#-*- coding:utf-8 -*-
import json
import os
from collections import defaultdict
from .base import WebService, export, register


@register([u'百词斩', u'Baicizhan'])
class Baicizhan(WebService):

    bcz_download_mp3 = True
    bcz_download_img = True

    def __init__(self):
        super(Baicizhan, self).__init__()

    def _get_from_api(self):
        word = self.word.replace(' ', '_')
        url = u"http://mall.baicizhan.com/ws/search?w={}".format(word)
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
    
    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_from_api().get(key, default)

    @export('PRON', 0)
    def fld_phonetic(self):
        word = self.word.replace(' ', '_')
        url = u'http://baicizhan.qiniucdn.com/word_audios/{}.mp3'.format(word)
        audio_name = 'bcz_%s.mp3' % self.word
        if self.bcz_download_mp3:
            if os.path.exists(audio_name) or self.download(url, audio_name, 5):
                # urllib.urlretrieve(url, audio_name)
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

    @export('PHON', 1)
    def fld_phon(self):
        return self._get_field('accent')

    @export('IMAGE', 2)
    def fld_img(self):
        url = self._get_field('img')
        if url and self.bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if os.path.exists(filename) or self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        #return self.get_anki_label(url, 'img')
        return ''

    @export([u'象形', u'Pictogram'], 3)
    def fld_df(self):
        url = self._get_field('df')
        if url and self.bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if os.path.exists(filename) or self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        #return self.get_anki_label(url, 'img')
        return ''

    @export(u'DEF', 6)
    def fld_mean(self):
        return self._get_field('mean_cn')

    @export(u'EXAMPLE', 4)
    def fld_st(self):
        return self._get_field('st')

    @export('TRANS', 5)
    def fld_sttr(self):
        return self._get_field('sttr')

    @export([u'单词tv', u'TV'], 7)
    def fld_tv_url(self):
        video = self._get_field('tv')
        if video:
            return self.get_anki_label(video, 'video')
        return ''
