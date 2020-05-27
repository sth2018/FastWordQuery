# -*- coding:utf-8 -*-

import os
import re
from bs4 import Tag
from ..base import *
from ...utils.misc import format_multi_query_word

@register([u'韦氏词典', u'Merriam-Webster'])
class MerriamWebster(WebService):

    def __init__(self):
        super(MerriamWebster, self).__init__()

    def _get_from_api(self):
        url = 'https://www.merriam-webster.com/dictionary/{}'.format(format_multi_query_word(self.quote_word))
        data = self.get_response(url)
        soup = parse_html(data)

        # Top Container
        word_info = {}

        sym_div = soup.find('div', {'id': 'synonyms-anchor'})
        for a in sym_div.findAll('a'):
            if 'thesaurus' not in a['href']:
                a['href'] = 'https://www.merriam-webster.com/dictionary{}'.format(a['href'])
            else:    
                a['href'] = 'https://www.merriam-webster.com{}'.format(a['href'])
        word_info['sa'] = str(sym_div)
        return self.cache_this(word_info)

    @export([u'同义词反义词', u'Synonyms & Antonyms'])
    @with_styles(cssfile='_mw.css')
    def fld_sa(self):
        return self._get_field('sa')
