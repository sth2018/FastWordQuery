#-*- coding:utf-8 -*-

import xml.etree.ElementTree
from ..base import *


@register([u'有道词典-韩语', u'Youdao-Korean'])
class Youdaoko(WebService):

    def __init__(self):
        super(Youdaoko, self).__init__()

    def _get_from_api(self, lang='ko'):
        url = (u'http://dict.youdao.com/fsearch?client=deskdict'
                    '&keyfrom=chrome.extension&pos=-1'
                    '&doctype=xml&xmlVersion=3.2'
                    '&dogVersion=1.0&vendor=unknown'
                    '&appVer=3.1.17.4208'
                    '&le={0}&q={1}').format(lang, self.quote_word)
        result ={
            'phonetic': '',
            'explains':'',
        }
        try:
            html = self.get_response(url, timeout=5)
            # showInfo(str(result))
            doc = xml.etree.ElementTree.fromstring(html)
            # fetch explanations
            explains = '<br>'.join([node.text for node in doc.findall(
                ".//custom-translation/translation/content")])
            result.update({'explains': explains})
        except:
            pass
        return self.cache_this(result)

    @export([u'基本释义', u'Explanations'])
    def fld_explains(self):
        return self.cache_result('explains') if self.cached('explains') else \
            self._get_from_api().get('explains', '')

    @with_styles(cssfile='_youdao.css', need_wrap_css=True, wrap_class='youdao')
    def _get_singledict(self, single_dict, lang='ko'):
        url = u"http://m.youdao.com/singledict?q={0}&dict={1}&le={2}&more=false".format(
            self.quote_word, single_dict, lang
        )
        try:
            html = self.get_response(url, timeout=5)
            return (u'<div id="{0}_contentWrp" class="content-wrp dict-container">'
                        '<div id="{1}" class="trans-container {2} ">{3}</div>'
                        '</div>'
                        '<div id="outer">'
                        '<audio id="dictVoice" style="display: none"></audio>'
                        '</div>').format(
                single_dict,
                single_dict,
                single_dict,
                html.decode('utf-8')
            )
        except:
            return ''

    @export([u'网络释义', u'Web translation'])
    def fld_web_trans(self):
        return self._get_singledict('web_trans')

    @export([u'双语例句', u'Biligual example'])
    def fld_blng_sents_part(self):
        return self._get_singledict('blng_sents_part')

    @export([u'百科', u'baike'])
    def fld_baike(self):
        return self._get_singledict('baike')

    @export([u'汉语词典(中)', u'Chinese dictionary'])
    def fld_hh(self):
        return self._get_singledict('hh')
