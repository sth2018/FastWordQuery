#-*- coding:utf-8 -*-

import os
import xml.etree.ElementTree
from ..base import *

js = '''
var initVoice = function () {
    var player = document.getElementById('dictVoice');
    document.addEventListener('click', function (e) {
        var target = e.target;
        if (target.hasAttribute('role') && target.getAttribute('role').indexOf('dict_audio_js') >= 0) {
            var url = target.getAttribute('data-rel');
            player.setAttribute('src', url);
            player.volume = 1;
            player.play();
            e.preventDefault();
        }
    }, false);
};
initVoice();
'''

youdao_download_mp3 = True


@register([u'有道词典-英汉', u'Youdao'])
class Youdao(WebService):

    def __init__(self):
        super(Youdao, self).__init__()

    def _get_from_api(self, lang='eng'):
        url = (u'http://dict.youdao.com/fsearch?client=deskdict'
                    '&keyfrom=chrome.extension&pos=-1'
                    '&doctype=xml&xmlVersion=3.2'
                    '&dogVersion=1.0&vendor=unknown'
                    '&appVer=3.1.17.4208'
                    '&le={0}&q={1}').format(lang, self.quote_word)
        result ={
            'phonetic': '',
            'us_phonetic': '',
            'uk_phonetic': '',
            'explains':'',
        }
        try:
            html = self.get_response(url, timeout=5)
            doc = xml.etree.ElementTree.fromstring(html)
            # fetch symbols
            symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
                ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
            if uk_symbol and us_symbol:
                phonetics = 'UK [%s]   US [%s]' % (uk_symbol, us_symbol)
                us_phonetics = '/%s/' % us_symbol
                uk_phonetics = '/%s/' % uk_symbol
                #phonetics = '/%s/' % (us_symbol)
            elif symbol:
                phonetics = '/%s/' % symbol
                us_phonetics = ''
                uk_phonetics = ''
            else:
                phonetics = ''
                us_phonetics = ''
                uk_phonetics = ''
            # fetch explanations
            explains = '<br>'.join([node.text
                                    for node in doc.findall(
                                        ".//custom-translation/translation/content"
                                    )])
            result.update({'phonetic': phonetics, 'us_phonetic': us_phonetics, 'uk_phonetic': uk_phonetics, 'explains': explains})
        except:
            pass
        return self.cache_this(result)

    @export('PHON')
    def fld_phonetic(self):
        return self._get_field('phonetic')

    @export('AME_PHON')
    def fld_phonetic_us(self):
        return self._get_field('us_phonetic')

    @export('BRE_PHON')
    def fld_phonetic_uk(self):
        return self._get_field('uk_phonetic')

    @export([u'基本释义', u'Explanations'])
    def fld_explains(self):
        return self._get_field('explains')

    @with_styles(cssfile='_youdao.css', js=js, need_wrap_css=True, wrap_class='youdao')
    def _get_singledict(self, single_dict, lang='eng'):
        url = u"http://m.youdao.com/singledict?q={0}&dict={1}&le={2}&more=false".format(
            self.quote_word,
            single_dict,
            lang
        )
        try:
            result = self.get_response(url, timeout=5)
            return (u'<div id="{0}_contentWrp" class="content-wrp dict-container">'
                        '<div id="{0}" class="trans-container {0} ">{1}</div>'
                        '</div>'
                        '<div id="outer">'
                        '<audio id="dictVoice" style="display: none"></audio>'
                        '</div>').format(
                single_dict, 
                result.decode('utf-8')
            )
        except:
            return ''

    @export('BRE_PRON')
    def fld_british_audio(self):
        audio_url = u'http://dict.youdao.com/dictvoice?audio={}&type=1'.format(self.quote_word)
        if youdao_download_mp3:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export('AME_PRON')
    def fld_american_audio(self):
        audio_url = u'http://dict.youdao.com/dictvoice?audio={}&type=2'.format(self.quote_word)
        if youdao_download_mp3:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export([u'柯林斯英汉', u'Collins'])
    def fld_collins(self):
        return self._get_singledict('collins')

    @export([u'21世纪', u'21st century'])
    def fld_ec21(self):
        return self._get_singledict('ec21')

    @export([u'英英释义', u'English-english dictionary'])
    def fld_ee(self):
        return self._get_singledict('ee')

    @export([u'网络释义', u'Web translation'])
    def fld_web_trans(self):
        return self._get_singledict('web_trans')

    @export([u'同根词', u'Related words'])
    def fld_rel_word(self):
        val = self._get_singledict('rel_word')
        if val is None or val == '' or u'词根：${rel_word.getStem()}' in str(val):
            return ' '
        return val

    @export([u'同近义词', u'Synonyms'])
    def fld_syno(self):
        return self._get_singledict('syno')

    @export([u'双语例句', u'Bilingual examples'])
    def fld_blng_sents_part(self):
        return self._get_singledict('blng_sents_part')

    @export([u'原生例句', u''])
    def fld_media_sents_part(self):
        return self._get_singledict('media_sents_part')

    @export([u'权威例句', u'Authoritative examples'])
    def fld_auth_sents_part(self):
        return self._get_singledict('auth_sents_part')

    @export([u'新英汉大辞典(中)', u'New english-chinese dictionary'])
    def fld_ce_new(self):
        return self._get_singledict('ce_new')

    @export([u'百科', u'baike'])
    def fld_baike(self):
        return self._get_singledict('baike')

    @export([u'汉语词典(中)', u'Chinese dictionary'])
    def fld_hh(self):
        return self._get_singledict('hh')

    @export([u'专业释义(中)', u'Professional translation'])
    def fld_special(self):
        return self._get_singledict('special')
