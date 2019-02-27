#-*- coding:utf-8 -*-
import os
from ..base import *

baidu_download_mp3 = True

@register([u'百度汉语', u'Baidu-Hanyu'])
class Baidu_Chinese(WebService):

    def __init__(self):
        super(Baidu_Chinese, self).__init__()

    def _get_from_api(self):
        url = u"http://dict.baidu.com/s?wd={}&ptype=zici#basicmean".format(self.quote_word)
        try:
            html = self.get_response(url, timeout=10)
            soup = parse_html(html)
        except:
            pass
        result = {
            'pinyin': '',
            'basicmean': '',
            'detailmean': '',
            'source': '',
            'example': '',
            'synonym': '',
            'antonym': '',
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
            tag = element.find_all('div', {'class': 'tab-content'})
            if tag:
                result['basicmean'] = u''.join(str(x) for x in tag)

        #详细释义
        element = soup.find('div', id='detailmean-wrapper')
        if element:
            tag = element.find_all('div', {'class': 'tab-content'})
            if tag:
                result['detailmean'] = u''.join(str(x) for x in tag)

        #出处
        element = soup.find('div', id='source-wrapper')
        if element:
            tag = element.find('div', {'class': 'tab-content'})
            if tag:
                result['source'] = u''.join(str(x) for x in tag)

        #例句
        element = soup.find('div', id='liju-wrapper')
        if element:
            tag = element.find('div', {'class': 'tab-content'})
            if tag:
                result['example'] = u''.join(str(x) for x in tag)

        #近义词
        element = soup.find('div', id='synonym')
        if element:
            tag = element.find('div', {'class': 'block'})
            if tag:
                element = tag.find_all('a')
                result['synonym'] = u' '.join(x.get_text() for x in element)
        #反义词
        element = soup.find('div', id='antonym')
        if element:
            tag = element.find('div', {'class': 'block'})
            if tag:
                element = tag.find_all('a')
                result['antonym'] = u' '.join(x.get_text() for x in element)
        #英文翻译
        element = soup.find('div', id='fanyi-wrapper')
        if element:
            tag = element.find_all('dt')
            if tag:
                result['fanyi'] = u'<br>'.join(x.get_text().strip() for x in tag)

        return self.cache_this(result)

    @with_styles(need_wrap_css=True, cssfile='_baidu.css')
    def _css(self, val):
        return val

    @export([u'拼音', u'Phoneticize'])
    def fld_pinyin(self):
        return self._get_field('pinyin')

    @export('PRON')
    def fld_pron(self):
        audio_url = self._get_field('audio_url')
        if baidu_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export([u'基本释义', u'Basic Definitions'])
    def fld_basic(self):
        val = self._get_field('basicmean')
        if val is None or val == '':
            return ''
        return self._css(val)

    @export([u'详细释义', u'Detail Definitions'])
    def fld_detail(self):
        val = self._get_field('detailmean')
        if val is None or val == '':
            return ''
        return self._css(val)

    @export([u'出处', u'Source Definitions'])
    def fld_source(self):
        val = self._get_field('source')
        if val is None or val == '':
            return ''
        return self._css(val)

    @export([u'例句', u'Example Definitions'])
    def fld_example(self):
        val = self._get_field('example')
        if val is None or val == '':
            return ''
        return self._css(val)
    @export([u'近义词', u'Synonym'])
    def fld_synonym(self):
        val = self._get_field('synonym')
        if val is None or val == '':
            return ''
        return self._css(val)

    @export([u'反义词', u'Antonym'])
    def fld_antonym(self):
        val = self._get_field('antonym')
        if val is None or val == '':
            return ''
        return self._css(val)

    @export([u'英文翻译', u'Translation[En]'])
    def fld_fanyi(self):
        return self._get_field('fanyi')
