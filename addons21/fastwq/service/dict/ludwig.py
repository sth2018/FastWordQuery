#-*- coding:utf-8 -*-
import random
from ..base import *

oxford_download_mp3 = True

@register(u'Ludwig')
class Ludwig(WebService):

    def __init__(self):
        super(Ludwig, self).__init__()

    def _get_from_api(self):
        data = self.get_response(u'https://ludwig.guru/s/{}'.format(self.quote_word))
        soup = parse_html(data)
        result = {
            'def': u'',
            'examples': []
        }

        # def
        element = soup.find('div', class_='-id-__definition--1E88I')
        if element:
            e_list = element.find_all('p')
            if e_list:
                result['def'] = u''.join(str(c) for c in e_list)

        # examples
        e_list = soup.find_all('p', class_='-id-__exact--SVDfq')
        if e_list:
            e_arr = []
            for n in e_list:
                e_arr.append(str(n.get_text()))
            result['examples'] = e_arr
        return self.cache_this(result)
    
    @export('DEF')
    def fld_definate(self):
        return self._get_field('def')

    @export('EXAMPLE')
    def fld_example(self):
        return self._range_examples([i for i in range(0, 100)])

    @export([u'随机例句', u'Random example'])
    def fld_random_example(self):
        return self._range_examples()

    @export([u'首2个例句', u'First 2 examples'])
    def fld_first2_example(self):
        return self._range_examples([0, 1])

    def _range_examples(self, range_arr=None):
        maps = self._get_field('examples')
        if maps:
            range_arr = range_arr if range_arr else [random.randrange(0, len(maps) - 1, 1)]
            my_str = u''
            for i,n in enumerate(maps):
                if i in range_arr:
                    my_str += u'<li>{}</li>'.format(n)
            return u'<ul>{}</ul>'.format(my_str)
        return u''
