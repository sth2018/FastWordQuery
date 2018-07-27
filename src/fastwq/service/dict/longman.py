#-*- coding:utf-8 -*-

from hashlib import sha1
from ..base import WebService, export, register, with_styles, parse_html
from ...libs.bs4 import Tag


longman_download_mp3 = True


@register([u'朗文', u'Longman'])
class Longman(WebService):

    def __init__(self):
        super(Longman, self).__init__()

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)
    
    def _get_content(self):
        url = 'https://www.ldoceonline.com/dictionary/{}'.format(self.word)
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
            am_s_tag = dic_link.find('span', title='Play American pronunciation of {}'.format(self.word))
            br_s_tag = dic_link.find('span', title='Play British pronunciation of {}'.format(self.word))
            if am_s_tag:
                word_info['am_mp3'] = am_s_tag.get('data-src-mp3', u'')
                am_s_tag.decompose()
            if br_s_tag:
                word_info['br_mp3'] = br_s_tag.get('data-src-mp3', u'')
                br_s_tag.decompose()

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
                #self.cache_this(word_info)
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

    @export(u'音标')
    def fld_phonetic(self):
        return self._get_field('phonetic')
    
    def _fld_mp3(self, fld):
        audio_url = self._get_field(fld)
        if longman_download_mp3 and audio_url:
            filename = u'_longman_{}_.mp3'.format(self.word)
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
            if self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export(u'美音')
    def fld_mp3_us(self):
        return self._fld_mp3('am_mp3')

    @export(u'英音')
    def fld_mp3_uk(self):
        return self._fld_mp3('br_mp3')

    @export(u'断字单词')
    def fld_hyphenation(self):
        return self._get_field('hyphenation')

    @export(u'词性')
    def fld_pos(self):
        return self._get_field('pos')

    @export(u'英英解释')
    @with_styles(cssfile='_longman.css')
    def fld_ee(self):
        return self._get_field('ee')

    @export(u'变形')
    @with_styles(cssfile='_longman.css')
    def fld_inflections(self):
        return self._get_field('inflections')
