#-*- coding:utf-8 -*-
import random
from ..base import *


@register(u'Vocabulary.com')
class Vocabulary(WebService):

    def __init__(self):
        super(Vocabulary, self).__init__()

    def _get_from_api(self):
        data = self.get_response(u'https://www.vocabulary.com/dictionary/{}'.format(self.quote_word))
        soup = parse_html(data)
        result = {
            'short': u'',
            'long': u'',
        }

        # short
        element = soup.find('p', class_='short')
        if element:
            result['short'] = u''.join(str(e) for e in element.contents)

        # long
        element = soup.find('p', class_='long')
        if element:
            result['long'] = u''.join(str(e) for e in element.contents)

        return self.cache_this(result)
    
    @export([u'简短释义', u'Short definition'])
    def fld_definate(self):
        return self._get_field('short')

    @export([u'详细释义', u'Long definition'])
    def fld_example(self):
        return self._get_field('long')
