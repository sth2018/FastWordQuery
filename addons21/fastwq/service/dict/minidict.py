#-*- coding:utf-8 -*-

from ..base import *


@register([u'海词迷你词典', u'dict.cn'])
class MiniDict(WebService):

    def __init__(self):
        super(MiniDict, self).__init__()

    def _get_from_api(self):
        data = self.get_response(u"http://apii.dict.cn/mini.php?q={}".format(self.quote_word))
        soup = parse_html(data)
        result = {
            'expressions': u'', 
            'sentences': u'', 
            'variations': u'',
            'phonetic': u'',
        }

        # 音标
        tag = soup.find('span', class_='p')
        if tag:
            result['phonetic'] = str(tag.get_text())
            tag.decompose()
        
        # 基本释义
        tag = soup.find('div', id='e')
        if tag:
            result['expressions'] = str(tag)
            tag.decompose()

        # 例句与用法
        tag = soup.find('div', id='s')
        if tag:
            result['sentences'] = str(tag)
            tag.decompose()

        # 词形变化
        tag = soup.find('div', id='t')
        if tag:
            result['variations'] = str(tag)
            tag.decompose()

        return self.cache_this(result)

    @export('PHON')
    def fld_phonetic(self):
        return self._get_field('phonetic')

    @export([u'基本释义', u'Expressions'])
    def fld_explains(self):
        return self._get_field('expressions')

    @export([u'例句与用法', u'Examples and patterns'])
    @with_styles(css='em {color:#cc0066;font-style:normal;}', need_wrap_css=True, wrap_class='minidict')
    def fld_sentences(self):
        return self._get_field('sentences')

    @export([u'词形变化', u'Inflections'])
    def fld_variations(self):
        return self._get_field('variations')
