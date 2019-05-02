# -*- coding:utf-8 -*-
import xml.etree.ElementTree
from ..base import WebService, export, register, with_styles
import requests
import hashlib
import random
import json


@register([u'百度翻译', u'Baidu-Translate'])
class BaiduFy(WebService):

    def __init__(self):
        super(BaiduFy, self).__init__()

    def _get_from_api(self, lang='fr'):
        url = u'http://api.fanyi.baidu.com/api/trans/vip/translate'
        result = {
                'explains': '',
            }
        data = {
                'q': '',
                'from': 'en',
                'to': 'zh',
                'appid': '20190502000293467',
                'salt': '',
                'sign': '',
            }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        }
        
        miyao = 'QEl8tPQXtgn35Dzxubk6'
        try:
            data['q'] = self.word
            data['salt'] = str(random.randint(0, 100))
            strs = data['appid'] + data['q'] + data['salt'] + miyao
            data['sign'] = hashlib.md5(strs.encode('utf-8')).hexdigest()
            html = requests.post(url, data=data, headers=headers)
            explains = json.loads(html.content)['trans_result'][0]['dst']
            result.update({'explains': explains})
        except:
            pass
        return self.cache_this(result)

    @export([u'翻译结果', 'translation'])
    def fld_explains(self):
        return self.cache_result('explains') if self.cached('explains') else \
            self._get_from_api().get('explains', '')
    @export([u'英式发音', 'uk'])
    def fld_uk_audio(self):
        audiourl = 'http://tts.baidu.com/text2audio?lan=uk&pid=101&ie=UTF-8&text={0}&spd=4'.format(self.quote_word)
        audio = requests.get(audiourl)
        name = 'bdfy_uk'+hashlib.md5(audiourl.encode('utf-8')).hexdigest()+'.mp3'
        with open(name,'wb') as f:
            f.write(audio.content)
        return self.get_anki_label(name, 'audio')
    @export([u'美式发音', 'en'])
    def fld_en_audio(self):
        audiourl = 'http://tts.baidu.com/text2audio?lan=en&pid=101&ie=UTF-8&text={0}&spd=4'.format(self.quote_word)
        audio = requests.get(audiourl)
        name = 'bdfy_en'+hashlib.md5(audiourl.encode('utf-8')).hexdigest()+'.mp3'
        with open(name,'wb') as f:
            f.write(audio.content)
        return self.get_anki_label(name, 'audio')