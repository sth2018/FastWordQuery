#-*- coding:utf-8 -*-
from hashlib import sha1
from .base import WebService, export, register, with_styles, parseHtml

baidu_download_mp3 = True

@register([u'百度汉语', u'Baidu Chinese'])
class Baidu_Chinese(WebService):

    def __init__(self):
        super(Baidu_Chinese, self).__init__()

    def _get_content(self):
        url = u"https://hanyu.baidu.com/s?wd={}&ptype=zici#basicmean".format(self.word)
        html = self.get_response(url, timeout=10)
        soup = parseHtml(html)
        result = {
            'pinyin': '',
            'basicmean': '',
            'detailmean': '',
            'fanyi': '',
            'audio_url': '',
        }

        #拼音
        element = soup.find('div', id='pinyin')
        if element:
            tag = element.find_all('b')
            if tag:
                result['pinyin'] = u' '.join(x.get_text() for x in tag)
            if tag:
                tag = element.find('a')
                if tag:
                    result['audio_url'] = tag.get('url')

        #基本释义
        element = soup.find('div', id='basicmean-wrapper')
        if element:
            tag = element.find_all('dl')
            if tag:
                result['basicmean'] = u''.join(str(x) for x in tag)

        #详细释义
        element = soup.find('div', id='detailmean-wrapper')
        if element:
            tag = element.find_all('dl')
            if tag:
                result['detailmean'] = u''.join(str(x) for x in tag)

        #英文翻译
        element = soup.find('div', id='fanyi-wrapper')
        if element:
            tag = element.find_all('dt')
            if tag:
                result['fanyi'] = u'<br>'.join(x.get_text().strip() for x in tag)

        return self.cache_this(result)

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @export([u'拼音', u'Phoneticize'], 1)
    def fld_pinyin(self):
        return self._get_field('pinyin')

    @export('PRON', 2)
    def fld_pron(self):
        audio_url = self._get_field('audio_url')
        if baidu_download_mp3 and audio_url:
            filename = u'_baidu_chinese_{}_.mp3'.format(self.word)
            hex_digest = sha1(
                self.word.encode('utf-8') if isinstance(self.word, unicode)
                else self.word
            ).hexdigest().lower()
            assert len(hex_digest) == 40, "unexpected output from hash library"
            filename = '.'.join([
                '-'.join([
                    self.unique.lower(
                    ), hex_digest[:8], hex_digest[8:16],
                    hex_digest[16:24], hex_digest[24:32], hex_digest[32:],
                ]),
                'mp3',
            ])
            try:
                self.net_download(
                    filename,
                    audio_url,
                    require=dict(mime='audio/mp3', size=512),
                )
                return self.get_anki_label(filename, 'audio')
            except:
                pass
        return ''

    @export([u'基本释义', u'Basic Definitions'], 3)
    def fld_basic(self):
        return self._get_field('basicmean')

    @export([u'详细释义', u'Detail Definitions'], 4)
    def fld_detail(self):
        return self._get_field('detailmean')

    @export([u'英文翻译', u'Translation[En]'], 5)
    def fld_fanyi(self):
        return self._get_field('fanyi')
