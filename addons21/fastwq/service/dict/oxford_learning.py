# coding=utf-8
# from warnings import filterwarnings

from bs4 import Tag
from ..base import *
from ...utils.misc import format_multi_query_word

#filterwarnings('ignore')

import sys

#reload(sys)
#sys.setdefaultencoding('utf8')

@register([u'牛津学习词典', u'Oxford Learner'])
class OxfordLearning(WebService):

    def __init__(self):
        super(OxfordLearning, self).__init__()

    def query(self, word):
        """
        :param word:
        :rtype:  WebWord
        """
        qry_url = u'https://www.oxfordlearnersdictionaries.com/definition/english/{}'.format(format_multi_query_word(word))

        retried = 10
        while retried:
            try:
                rsp = self.get_response(qry_url, timeout=15)
                if rsp:
                    return OxfordLearningDictWord(rsp)
                break
            except:
                retried -= 1
                continue

    def _get_single_dict(self, single_dict):
        if not (self.cached(single_dict) and self.cache_result(single_dict)):
            web_word = self.query(self.quote_word)
            if web_word:
                self.cache_this(
                    {
                        'phonetic': '{} {}'.format(web_word.wd_phon_bre, web_word.wd_phon_ame),
                        'phon_bre': '{}'.format(web_word.wd_phon_bre),
                        'phon_ame': '{}'.format(web_word.wd_phon_ame),
                        'phon_bre_no_prefix': '{}'.format(web_word.wd_phon_bre_no_prefix),
                        'phon_ame_no_prefix': '{}'.format(web_word.wd_phon_ame_no_prefix),
                        'pos': web_word.wd_pos,
                        'img_full': web_word.wd_image_full_url,
                        'img_thumb': web_word.wd_image_thumb_url,
                        'ee': ''.join(web_word.definitions_html),
                        's_bre': web_word.wd_sound_url_bre,
                        's_ame': web_word.wd_sound_url_nam,
                    }
                )
            else:
                self.cache_this(
                    {
                        'phonetic': '',
                        'phon_bre': '',
                        'phon_ame': '',
                        'pos': '',
                        'img_full': '',
                        'img_thumb': '',
                        'ee': '',
                        's_bre': '',
                        's_ame': '',
                    }
                )
        return self.cache_result(single_dict)

    @export('PHON')
    def fld_phonetic(self):
        return self._get_single_dict('phonetic')

    @export('AME_PHON')
    def fld_phonetic_us(self):
        return self._get_single_dict('phon_ame')

    @export('BRE_PHON')
    def fld_phonetic_uk(self):
        return self._get_single_dict('phon_bre')

    @export('BRE_PHON_NO_PREFIX')
    def fld_phonetic_us_no_prefix(self):
        return self._get_single_dict('phon_bre_no_prefix')

    @export('AME_PHON_NO_PREFIX')
    def fld_phonetic_uk_no_prefix(self):
        return self._get_single_dict('phon_ame_no_prefix')

    @export([u'词性', u'POS'])
    def fld_pos(self):
        return self._get_single_dict('pos')

    @export('DEF')
    @with_styles(cssfile='_oxford.css')
    def fld_ee(self):
        # return '<div style="margin-left: 20px">' + self._get_single_dict(
        #     'ee') + "</div>" if "<li>" not in self._get_single_dict('ee') else self._get_single_dict('ee')
        return self._get_single_dict('ee')

    def get_image_full(self):
        url = self._get_single_dict('img_full')
        filename = get_hex_name(self.unique.lower(), url, 'jpg')
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'img')
        return ''

    def get_image_thumb(self):
        url = self._get_single_dict('img_thumb')
        filename = get_hex_name(self.unique.lower(), url, 'jpg')
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'img')
        return ''

    def get_sound_bre(self):
        url = self._get_single_dict('s_bre')
        filename = get_hex_name(self.unique.lower(), url, 'mp3')
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'audio')
        return ''

    def get_sound_ame(self):
        url = self._get_single_dict('s_ame')
        filename = get_hex_name(self.unique.lower(), url, 'mp3')
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'audio')
        return ''

    @export('IMAGE')
    def fld_image_full(self):
        return self.get_image_full()

    @export([u'缩略图', u'Thumbnails'])
    def fld_image_thumb(self):
        return self.get_image_thumb()

    @export('BRE_PRON')
    def fld_sound_bre(self):
        return self.get_sound_bre()

    @export('AME_PRON')
    def fld_sound_ame(self):
        return self.get_sound_ame()

    @export([u'英式发音优先', u'British Pronunciation First'])
    def fld_sound_pri(self):
        bre = self.get_sound_bre()
        return bre if bre else self.get_sound_ame()


class OxfordLearningDictWord:

    def __init__(self, markups):
        if not markups:
            return
        self.markups = markups
        self.bs = parse_html(self.markups)
        self._defs = []
        self._defs_html = []

    @staticmethod
    def _cls_dic(class_nm):
        return {'class': class_nm}

    # region Tags
    @property
    def tag_web_top(self):
        """

        word - class: h
        pos - class: pos

        :rtype: Tag
        """
        return self.bs.find("div", self._cls_dic('webtop-g'))

    @property
    def tag_img(self):
        """

        :rtype: Tag
        """
        return self.bs.find('a', self._cls_dic('topic'))

    @property
    def tag_pron(self):
        """

        :rtype: Tag
        """
        return self.bs.find("div", self._cls_dic('pron-gs ei-g'))

    @property
    def tag_phon_bre(self):
        """

        :rtype: Tag
        """
        return self.tag_pron.find('span', self._cls_dic('pron-g'), geo='br')

    @property
    def tag_phon_nam(self):
        """

        :rtype: Tag
        """
        return self.tag_pron.find('span', self._cls_dic('pron-g'), geo='n_am')

    # ---- Explains
    @property
    def tag_explain(self):
        """

        :rtype: Tag
        """
        return self.bs.find('span', self._cls_dic('sn-gs'))

    # endregion

    def _pull_bre_phon(self):
        try:
            _tag_phn = self.tag_phon_bre.find('span', self._cls_dic('phon')).get_text().replace('/', '').replace('BrE', '')
            phon = '/{}/'.format(_tag_phn.text if isinstance(_tag_phn, Tag) else _tag_phn)
        except:
            phon = ''
        return phon

    @property
    def wd_phon_bre_no_prefix(self):
        """

        :return: phon
        """
        return self._pull_bre_phon()

    @property
    def wd_phon_bre(self):
        """

        :return: pre_fix, phon
        """
        try:
            prefix = self.tag_phon_bre.find('span', self._cls_dic('prefix')).string
        except:
            prefix = ''
        return "{} {}".format(
            prefix,
            self._pull_bre_phon()
        )

    @property
    def wd_pos(self):
        try:
            return self.tag_web_top.find("span", 'pos').text
        except:
            return ''

    def _pull_ame_phon(self):
        try:
            _tag_phn = self.tag_phon_nam.find('span', self._cls_dic('phon')).get_text().replace('/', '').replace('NAmE', '')
            phon = '/{}/'.format(_tag_phn.text if isinstance(_tag_phn, Tag) else _tag_phn)
        except:
            phon = ''
        return phon

    @property
    def wd_phon_ame_no_prefix(self):
        """

        :return: phon
        """
        return self._pull_ame_phon()

    @property
    def wd_phon_ame(self):
        """

        :return: pre_fix, phon
        """
        try:
            prefix = self.tag_phon_nam.find('span', self._cls_dic('prefix')).string
        except:
            prefix = ''
        return "{} {}".format(
            prefix,
            self._pull_ame_phon()
        )

    @property
    def wd_image_full_url(self):
        try:
            return self.tag_img['href']
        except:
            return ''

    @property
    def wd_image_thumb_url(self):
        try:
            return self.tag_img.find('img', self._cls_dic('thumb'))['src']
        except:
            return ''

    @property
    def wd_sound_url_bre(self):
        try:
            return self.tag_phon_bre.find('div', self._cls_dic('sound audio_play_button pron-uk icon-audio'))[
                'data-src-mp3']
        except:
            return ''

    @property
    def wd_sound_url_nam(self):
        try:
            return self.tag_phon_nam.find('div', self._cls_dic('sound audio_play_button pron-us icon-audio'))[
                'data-src-mp3']
        except:
            return ''

    def get_definitions(self):
        defs = []
        defs_html = []
        if self.tag_explain and not self._defs:
            tag_exp = self._clean(self.tag_explain)
            lis = [li for li in tag_exp.find_all('li')]
            if not lis:
                defs_html.append(str(tag_exp.prettify()))
                defs.append(tag_exp.text)

            else:
                for li in lis:
                    defs_html.append(str(li.prettify()))
                    defs.append(li.text)
            self._defs = defs
            self._defs_html = defs_html
        return self._defs, self._defs_html

    @property
    def definitions(self):
        return self.get_definitions()[0]

    @property
    def definitions_html(self):
        return self.get_definitions()[1]

    def _clean(self, tg):
        """

        :type tg:Tag
        :return:
        """
        if not tg:
            return tg
        decompose_cls = ['xr-gs', 'sound', 'heading', 'topic', 'collapse', 'oxford3000']

        if tg.attrs and 'class' in tg.attrs:
            for _cls in decompose_cls:
                _tgs = tg.find_all(attrs=self._cls_dic(_cls), recursive=True)
                for _tg in _tgs:
                    _tg.decompose()

        rmv_attrs = ['dpsid', 'id', 'psg', 'reg']
        try:
            tg.attrs = {key: value for key, value in tg.attrs.items()
                        if key not in rmv_attrs}
        except ValueError:
            pass
        for child in tg.children:
            if not isinstance(child, Tag):
                continue
            self._clean(child)
        return tg
