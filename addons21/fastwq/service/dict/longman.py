# -*- coding:utf-8 -*-

import os
import re
from bs4 import Tag
from ..base import *
from ...utils.misc import format_multi_query_word

longman_download_mp3 = True
longman_download_img = True


@register([u'朗文', u'Longman'])
class Longman(WebService):

    def __init__(self):
        super(Longman, self).__init__()

    def _get_from_api(self):
        url = 'https://www.ldoceonline.com/dictionary/{}'.format(format_multi_query_word(self.quote_word))
        data = self.get_response(url)
        soup = parse_html(data)
        # Top Container
        dictlinks = soup.find_all('span', {'class': 'dictlink'})
        body_html = ""
        word_info = {}
        head_finded = False
        for dic_link in dictlinks:
            assert isinstance(dic_link, Tag)

            # remove sound tag
            am_s_tag = dic_link.find('span', {'class': 'speaker amefile fa fa-volume-up hideOnAmp'})
            br_s_tag = dic_link.find('span', {'class': 'speaker brefile fa fa-volume-up hideOnAmp'})
            if am_s_tag:
                word_info['am_mp3'] = am_s_tag.get('data-src-mp3', u'')
                am_s_tag.decompose()
            if br_s_tag:
                word_info['br_mp3'] = br_s_tag.get('data-src-mp3', u'')
                br_s_tag.decompose()

            # remove image
            image_tag = dic_link.find('img')
            if image_tag:
                word_info['image'] = image_tag.get('src', u'')
                image_tag.decompose()

            # Remove related Topics Container
            related_topic_tag = dic_link.find('div', {'class': "topics_container"})
            if related_topic_tag:
                related_topic_tag.decompose()

            # Remove Tail
            tail_tag = dic_link.find("span", {'class': 'Tail'})
            if tail_tag:
                tail_tag.decompose()

            # Remove SubEntry
            sub_entries = dic_link.find_all('span', {'class': 'SubEntry'})
            for sub_entry in sub_entries:
                sub_entry.decompose()

            # word elements
            head_tag = dic_link.find('span', {'class': "Head"})
            if head_tag and not head_finded:
                try:
                    hyphenation = head_tag.find("span", {'class': 'HYPHENATION'}).string  # Hyphenation
                except:
                    hyphenation = u''
                try:
                    pron_codes = u''.join(
                        list(head_tag.find("span", {'class': 'PronCodes'}).strings))  # Hyphenation
                except:
                    pron_codes = u''
                try:
                    POS = head_tag.find("span", {'class': 'POS'}).string  # Hyphenation
                except:
                    POS = u''

                try:
                    Inflections = head_tag.find('span', {'class': 'Inflections'})
                    if Inflections:
                        Inflections = str(Inflections)
                    else:
                        Inflections = u''
                except:
                    Inflections = u''

                word_info['phonetic'] = pron_codes
                word_info['hyphenation'] = hyphenation
                word_info['pos'] = POS
                word_info['inflections'] = Inflections
                head_finded = True
                # self.cache_this(word_info)
            if head_tag:
                head_tag.decompose()

            # remove script tag
            script_tags = dic_link.find_all('script')
            for t in script_tags:
                t.decompose()

            # remove img tag
            img_tags = dic_link.find_all('img')
            for t in img_tags:
                t.decompose()

            # remove example sound tag
            emp_s_tags = dic_link.find_all('span', {'class': 'speaker exafile fa fa-volume-up'})
            for t in emp_s_tags:
                t.decompose()

            body_html += str(dic_link)

        word_info['ee'] = body_html
        return self.cache_this(word_info)

    @export('PHON')
    def fld_phonetic(self):
        return self._get_field('phonetic')

    def _fld_mp3(self, fld):
        audio_url = self._get_field(fld)
        if longman_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    def _fld_img(self, fld):
        img_url = self._get_field(fld)
        if longman_download_img and img_url:
            # img_url -> https://.../ldoce_XXX.jpg?version=A.B.CC
            img_url_no_version = re.sub(r'\?version=.*?$', '', img_url)
            # file extension isn't always jpg
            file_extension = os.path.splitext(img_url_no_version)[1][1:].strip().lower()
            filename = get_hex_name(self.unique.lower(), img_url, file_extension)
            if os.path.exists(filename) or self.net_download(filename, img_url):
                return self.get_anki_label(filename, 'img')
        return ''

    @export(u'AME_PRON')
    def fld_mp3_us(self):
        return self._fld_mp3('am_mp3')

    @export(u'BRE_PRON')
    def fld_mp3_uk(self):
        return self._fld_mp3('br_mp3')

    @export('IMAGE')
    def fld_image(self):
        return self._fld_img('image')

    @export([u'断字单词', u'Hyphenation'])
    def fld_hyphenation(self):
        return self._get_field('hyphenation')

    @export([u'词性', u'POS'])
    def fld_pos(self):
        return self._get_field('pos')

    @export('DEF')
    @with_styles(cssfile='_longman.css')
    def fld_ee(self):
        return self._get_field('ee')

    @export([u'变形', u'Inflections'])
    @with_styles(cssfile='_longman.css')
    def fld_inflections(self):
        return self._get_field('inflections')
