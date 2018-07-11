#-*- coding:utf-8 -*-
import re
from .base import WebService, export, register, with_styles, parseHtml

bing_download_mp3 = True

@register([u'Bing', u'Bing'])
class Bing(WebService):

    def __init__(self):
        super(Bing, self).__init__()

    def _get_content(self):
        word = self.word.replace(' ', '_')
        data = self.get_response(u"http://cn.bing.com/dict/search?q={}&mkt=zh-cn".format(word))
        soup = parseHtml(data)
        result = {
            'pronunciation': {'AmE': '', 'BrE': '', 'AmEmp3': '', 'BrEmp3': ''},
            'def': '',
            'sams': '',
        }

        #音
        element = soup.find('div', class_='hd_tf_lh')
        if element:
            audios = element.find_all('a')
            #美式英标
            tag = element.find('div', class_='hd_pr')
            if tag:
                result['pronunciation']['AmE'] = str(tag).decode('utf-8')
                #美音
                if audios:
                    tag = audios[0]
                    audio_url = tag.get('onclick')
                    if audio_url:
                        result['pronunciation']['AmEmp3'] = u''.join(re.findall(r'https://.*\.mp3', audio_url))

            #英式音标
            tag = element.find('div', class_='hd_prUS')
            if tag:
                result['pronunciation']['BrE'] = str(tag).decode('utf-8')
                #英音
                if audios:
                    tag = audios[1]
                    audio_url = tag.get('onclick')
                    if audio_url:
                        result['pronunciation']['BrEmp3'] = u''.join(re.findall(r'https://.*\.mp3', audio_url))

        #释义
        element = soup.find('div', class_='qdef')
        if element:
            element = getattr(element, 'ul', '')
            if element:
                result['def'] = u''.join([str(content) for content in element.contents])

        #例句 
        element = soup.find('div', id='sentenceSeg')
        if element:
            #英文例句
            tags = element.find_all('div', {"class": 'sen_en'})
            result['sams'] = [{'eng': u''.join(tag.find_all(text=True))} for tag in tags]
            #例句翻译
            tags = element.find_all('div', {"class": 'sen_cn'})
            for i, tag in enumerate(tags):
                result['sams'][i]['chn'] = u''.join(tag.find_all(text=True))

        return self.cache_this(result)

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @with_styles(css='.pos{font-weight:bold;margin-right:4px;}', need_wrap_css=True, wrap_class='bing')
    def _css(self, val):
        return val

    @export('AME_PHON', 1)
    def fld_phonetic_us(self):
        seg = self._get_field('pronunciation')
        return seg.get('AmE', u'')

    @export('BRE_PHON', 2)
    def fld_phonetic_uk(self):
        seg = self._get_field('pronunciation')
        return seg.get('BrE', u'')

    def _fld_mp3(self, fld):
        audio_url = self._get_field('pronunciation')[fld]
        if bing_download_mp3 and audio_url:
            filename = u'bing_' + u''.join(re.findall(r'\w*\.mp3', audio_url))
            if filename and self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('AME_PRON', 3)
    def fld_mp3_us(self):
        return self._fld_mp3('AmEmp3')

    @export('BRE_PRON', 4)
    def fld_mp3_uk(self):
        return self._fld_mp3('BrEmp3')
    
    @export('DEF', 5)
    def fld_definition(self):
        val = self._get_field('def')
        if val == None or val == '':
            return ''
        return self._css(val)

    @export('EXAMPLE', 6)
    def fld_samples(self):
        max_numbers = 10
        segs = self._get_field('sams')
        sentences = ''
        for i, seg in enumerate(segs):
            sentences += u"""<li><div class="se_li1">
                            <div class="sen_en">{0}.{1}</div>
                            <div class="sen_cn">{2}</div>
                        </div></li>""".format(i+1, seg['eng'], seg['chn'])
            if i == 9:
                break
        if sentences:
            return u"""<div class="se_div">
                            <div class="sentenceCon">
                                <div id="sentenceSeg"><ol>{0}</ol></div>
                            </div>
                    </div>""".format(sentences)
        return ''
