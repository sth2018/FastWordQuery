#-*- coding:utf-8 -*-
import os
import re

from ..base import *

cambridge_url_base = u'https://dictionary.cambridge.org/'
cambridge_download_mp3 = True
cambridge_download_img = True

class Cambridge(WebService):

    def __init__(self):
        super(Cambridge, self).__init__()

    def _get_url(self):
        return cambridge_url_base

    def _get_from_api(self):
        data = self.get_response(u'{0}{1}'.format(self._get_url(), self.quote_word))
        soup = parse_html(data)
        result = {
            'pronunciation': {'AmE': '', 'BrE': '', 'AmEmp3': '', 'BrEmp3': ''},
            'image': '',
            'thumb': '',
            'def': '',
            'def_list': []
        }

        #english
        element = soup.find('div', class_='di-body')
        if element:
            #页
            elements = element.find_all('div', class_='entry-body__el clrd js-share-holder')
            header_found = False
            for element in elements:
                if element:
                    #音
                    if not header_found:
                        header = element.find('div', class_='pos-header')
                        if header:
                            tags = header.find_all('span', class_=re.compile("uk|us"))
                            if tags:
                                for tag in tags:
                                    r = tag.find('span', class_='region')
                                    reg = r.get_text() if r else u''
                                    pn = 'AmE' if reg=='us' else 'BrE'
                                    p = tag.find('span', class_='pron')
                                    result['pronunciation'][pn] = p.get_text() if p else u''
                                    snd = tag.find('span', class_='circle circle-btn sound audio_play_button')
                                    if snd:
                                        result['pronunciation'][pn+'mp3'] = cambridge_url_base + snd.get('data-src-mp3')
                                    header_found = True
                    #义
                    body = element.find('div', class_='pos-body')
                    if body:
                        tags = body.find_all('div', class_='def-block pad-indent')
                        if tags:
                            l = result['def_list']
                            for tag in tags:
                                i = tag.find('span', class_='def-info')
                                d = tag.find('b', class_='def')
                                trans = tag.find('span', class_='trans')
                                es = tag.find_all('div', class_='examp emphasized')
                                l.append(
                                    u'<li>{0}{1}{2}{3}</li>'.format(
                                        u'<span class="epp-xref">{0}</span>'.format(i.get_text()) if i else u'',
                                        u'<b class="def">{0}</b>'.format(d.get_text()) if d else u'',
                                        u'<span class="trans">{0}</span>'.format(trans.get_text()) if trans else u'',
                                        u''.join(
                                            u'<div class="examp">{0}</div>'.format(e.get_text()) if e else u''
                                            for e in es
                                        )
                                    )
                                )
                            result['def'] = u'<ul>' + u''.join(s for s in l) + u'</ul>'
                        img = body.find('img', class_='lightboxLink')
                        if img:
                            result['image'] = cambridge_url_base + img.get('data-image')
                            result['thumb'] = cambridge_url_base + img.get('src')

        return self.cache_this(result)

    @with_styles(need_wrap_css=True, cssfile='_cambridge.css')
    def _css(self, val):
        return val

    @export('AME_PHON')
    def fld_phonetic_us(self):
        seg = self._get_field('pronunciation')
        return seg.get('AmE', u'') if seg else u''

    @export('BRE_PHON')
    def fld_phonetic_uk(self):
        seg = self._get_field('pronunciation')
        return seg.get('BrE', u'') if seg else u''

    def _fld_img(self, fld):
        image_url = self._get_field(fld)
        if cambridge_download_img and image_url:
            filename = get_hex_name(self.unique.lower(), image_url, 'jpg')
            if os.path.exists(filename) or self.net_download(filename, image_url):
                return self.get_anki_label(filename, 'img')
        return ''

    def _fld_mp3(self, fld):
        audio_url = self._get_field('pronunciation')[fld]
        if cambridge_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('IMAGE')
    def fld_image(self):
        return self._fld_img('image')

    @export([u'缩略图', u'Thumbnails'])
    def fld_thumbnail(self):
        return self._fld_img('thumb')

    @export('AME_PRON')
    def fld_mp3_us(self):
        return self._fld_mp3('AmEmp3')

    @export('BRE_PRON')
    def fld_mp3_uk(self):
        return self._fld_mp3('BrEmp3')

    @export('DEF')
    def fld_definition(self):
        val = self._get_field('def')
        if val == None or val == '':
            return ''
        return self._css(val)
