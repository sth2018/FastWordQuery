#-*- coding:utf-8 -*-
import os
import json
from ..base import *


@register([u'必应图片', u'Bing-Images'])
class Bing_Images(WebService):

    bing_download_img = True

    def __init__(self):
        super(Bing_Images, self).__init__()

    def _get_from_api(self):
        url = u"http://cn.bing.com/images/search?q={}".format(self.quote_word)
        html = self.get_response(url, timeout=10)
        soup = parse_html(html)
        result = {
            'img': '',
        }

        #图片连接
        tag = soup.find('a', class_='iusc')
        if tag:
            try:
                data = json.loads(tag.get('m'))
                result['img'] = data.get('turl', u'')
            except:
                pass

        return self.cache_this(result)

    @export([u'图片', u'Image'])
    def fld_pinyin(self):
        url = self._get_field('img')
        if url and self.bing_download_img:
            filename = get_hex_name(self.unique.lower(), url, 'jpg')
            if os.path.exists(filename) or self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        return ''
