#-*- coding:utf-8 -*-
from hashlib import sha1
from ..base import WebService, export, register, with_styles, parse_html

cambridge_download_mp3 = True

@register([u'剑桥英英', u'Cambridge'])
class Cambridge(WebService):

    def __init__(self):
        super(Cambridge, self).__init__()

    def _get_content(self):
        word = self.word.replace(' ', '_')
        data = self.get_response(u"https://dictionary.cambridge.org/dictionary/english/{}".format(word))
        soup = parse_html(data)
        result = {
            'pronunciation': {'AmE': '', 'BrE': '', 'AmEmp3': '', 'BrEmp3': ''},
            'def': '',
            'sams': '',
        }

        #页
        element = soup.find('div', class_='entry-body__el clrd js-share-holder')
        if element:
            #音
            header = element.find('div', class_='pos-header')
            if header:
                tags = header.find_all('span', class_='pron-info')
                if tags:
                    for tag in tags:
                        reg = str(tag.find('span', class_='region').get_text()).decode('utf-8')
                        pn = 'AmE' if reg=='us' else 'BrE'
                        result['pronunciation'][pn] = str(tag.find('span', class_='pron').get_text()).decode('utf-8')
                        snd = tag.find('span', class_='circle circle-btn sound audio_play_button')
                        if snd:
                            result['pronunciation'][pn+'mp3'] = u'https://dictionary.cambridge.org' + snd.get('data-src-mp3')
            #义
            body = element.find('div', class_='pos-body')
            if body:
                tags = body.find_all('div', class_='def-block pad-indent')
                if tags:
                    l = []
                    for tag in tags:
                        l.append(
                            u'<li><span class="epp-xref">{0}</span>\
                            <b class="def">{1}</b>\
                            <div class="examp">{2}</div></li>'.format(
                                str(tag.find('span', class_='def-info').get_text()).decode('utf-8'),
                                str(tag.find('b', class_='def').get_text()).decode('utf-8'),
                                str(tag.find('div', class_='examp emphasized').get_text()).decode('utf-8')
                            )
                        )
                    result['def'] = u'<ul>' + u''.join(s for s in l) + u'</ul>'

        return self.cache_this(result)

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)
    
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

    def _fld_mp3(self, fld):
        audio_url = self._get_field('pronunciation')[fld]
        if cambridge_download_mp3 and audio_url:
            filename = u'_cambridge_{}_.mp3'.format(self.word)
            hex_digest = sha1(
                self.word.encode('utf-8') if isinstance(self.word, unicode)
                else self.word
            ).hexdigest().lower()
            assert len(hex_digest) == 40, "unexpected output from hash library"
            filename = '.'.join([
                '-'.join([
                    self.unique.lower(
                    ), hex_digest[:8], hex_digest[8:16],
                    hex_digest[16:24], hex_digest[24:32], hex_digest[32:],
                ]),
                'mp3',
            ])

            if filename and self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

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
