#-*- coding:utf-8 -*-
import os
import re
import random
from ..base import *

VOICE_PATTERN = r'<a href="sound://([\w/]+\w*\.mp3)"><img src="img/spkr_%s.png"></a>'
VOICE_PATTERN_WQ = r'<span class="%s"><a href="sound://([\w/]+\w*\.mp3)">(.*?)</span %s>'
MAPPINGS = [
    ['br', [re.compile(VOICE_PATTERN % r'r'), re.compile(
        VOICE_PATTERN_WQ % (r'brevoice', r'brevoice'))]],
    ['us', [re.compile(VOICE_PATTERN % r'b'), re.compile(
        VOICE_PATTERN_WQ % (r'amevoice', r'amevoice'))]]
]
LANG_TO_REGEXPS = {lang: regexps for lang, regexps in MAPPINGS}
# u'E:\\BaiduYunDownload\\mdx\\L6mp3.mdx'
DICT_PATH = u'C:\\dict\\OALD8\\牛津高阶8简体.mdx'


@register([u'本地词典-OALD8', u'MDX-OALD8'])
class OALD8(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'OALD8'):
                    dict_path = service.dict_path
                    break
        super(OALD8, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    @export([u'默认', u'Default'])
    def fld_whole(self):
        ''' 这个函数必须重新声明，否则第一个字段会被吞掉 '''
        html = self.get_default_html()
        js = re.findall(r'<script .*?>(.*?)</script>', html, re.DOTALL)
        jsfile = re.findall(
            r'<script .*?src=[\'\"](.+?)[\'\"]', html, re.DOTALL)
        return QueryResult(result=html, js=u'\n'.join(js), jsfile=jsfile)

    def get_html(self):
        """get self.word's html page from MDX"""
        if not self.html_cache[self.word]:
            html = self._get_definition_mdx()
            if html:
                self.html_cache[self.word] = html
        return self.html_cache[self.word]

    def _get_definition_mdx(self, word=''):
        """according to the word return mdx dictionary page"""
        if not word:
            word = self.word
        ignorecase = config.ignore_mdx_wordcase and (
            self.word != self.word.lower() or self.word != self.word.upper())
        content = self.builder.mdx_lookup(word, ignorecase=ignorecase)
        str_content = ""
        if len(content) > 0:
            for c in content:
                if c.upper().find(u"@@@LINK=") > -1:
                    word = c[len(u"@@@LINK="):].strip()
                    str_content += c.replace(u"@@@LINK="+word, "")
                    str_content += self._get_definition_mdx(word)
                else:
                    str_content += c.replace("\r\n", "").replace("entry:/", "")

        return str_content

    def _fld_phonetic(self, html, voice):
        ''' 获取音标 '''
        html = self.get_html()
        if voice == 'gb':
            m = re.search(
                r'<span.*?level="4".*?class="phon-gb">(.*?)</span>', html)
            if m:
                return m.groups()[0]
        elif voice == 'us':
            m = re.search(
                r'<span.*?level="4".*?class="phon-us">(.*?)</span>', html)
            if m:
                return m.groups()[0]
        return ''

    @export('BRE_PHON')
    def fld_phonetic_gb(self):
        ''' 英式音标 '''
        return self._fld_phonetic(self.get_html(), 'gb')

    @export('AME_PHON')
    def fld_phonetic_us(self):
        ''' 美式音标 '''
        return self._fld_phonetic(self.get_html(), 'us')

    def _fld_voice(self, html, voice):
        """获取发音字段"""
        soup = parse_html(html)
        voice_links = soup.findAll('a', attrs={'class': 'fayin'})
        sound_name = ''
        safe_word = self.word
        if '-' in safe_word or ' ' in safe_word:
            safe_word = safe_word.replace('-', '_').lower()
            safe_word = safe_word.replace(' ', '_').lower()
        for voice_link in voice_links:
            source_link = voice_link['href']
            if safe_word in source_link and voice in source_link:
                val = source_link.split(':')[-1][1:]
                name = get_hex_name('mdx-'+self.unique.lower(), val, 'spx')
                sound_name = self.save_file(val, name)
                if name:
                    return self.get_anki_label(sound_name, 'audio')

        return ''

    @export('BRE_PRON')
    def fld_voicebre(self):
        return self._fld_voice(self.get_html(), 'uk')

    @export('AME_PRON')
    def fld_voiceame(self):
        return self._fld_voice(self.get_html(), 'us')

    def _fld_image(self, img):
        val = img
        # file extension isn't always jpg
        file_extension = os.path.splitext(img)[1][1:].strip().lower()
        name = get_hex_name('mdx-'+self.unique.lower(), val, file_extension)
        name = self.save_file(val, name)
        if name:
            return self.get_anki_label(name, 'img')
        return ''

    @export('IMAGE')
    def fld_image(self):
        html = self.get_html()
        m = re.search(
            r'<img.*?src="(/thumb.*?)".*?alt.*?>', html)
        if m:
            return self._fld_image(m.groups()[0])
        return ''

    @export('DEF')
    def fld_definate(self):
        ''' 提取汉语释义 '''

        soup = parse_html(self.get_html())

        def get_dr(m_list, present_part):
            dr_list = present_part.findAll(
                'span', attrs={'eid': True, 'id': True, 'class': 'dr-g'})
            if dr_list:
                for dr_container in dr_list:
                    dr = dr_container.find(
                        'span', attrs={'class': ['dr', 'zd']})
                    if dr:
                        dr = dr.text
                    else:
                        dr = ''
                    dr_part = dr_container.find(
                        'span', attrs={'class': 'pos-g'})
                    if dr_part:
                        dr_part = ' -->' + dr_part.text
                    else:
                        dr_part = ''
                m_list.append([3, dr+dr_part])

        def get_phrase_def(m_list, soup):
            # 提取短语解释
            phrase_title = soup.find(
                'span', attrs={'class': 'id'})
            if not phrase_title:
                phrase_title = soup.find(
                    'span', attrs={'class': 'pv'})
            if phrase_title:
                title = phrase_title.text
                m_list.append([1, title])
                phrase_def_soup_list = soup.findAll(
                    'span', attrs={'class': 'def-g'})
                if phrase_def_soup_list:
                    for phrase_def_soup in phrase_def_soup_list:
                        bi_lng_def_list = phrase_def_soup.findAll(
                            'span', attrs={'class': {'d', 'ud'}})
                        if bi_lng_def_list:
                            for bi_lng_def in bi_lng_def_list:
                                chn_def = bi_lng_def.find('span')
                                if chn_def:
                                    m_list.append([2, chn_def.text])
                        else:
                            bi_lng_def_list = soup.findAll(
                                'span', attrs={'class': 'd'})
                            if bi_lng_def_list:
                                for bi_lng_def in bi_lng_def_list:
                                    child = bi_lng_def.find('span')
                                    if not child:
                                        m_list.append([2, bi_lng_def.text])

        def get_def_list(m_list, present_part):
            def_list = present_part.findAll(
                'span', attrs={'level': '2', 'class': 'n-g'})
            if def_list:
                # 有多个def
                for definition in def_list:
                    # 双语解释
                    def_bi_lng = definition.find(
                        'span', attrs={'class': 'def-g'})

                    if def_bi_lng:
                        # 提取汉语
                        chn_def = def_bi_lng.findAll(
                            'span', attrs={'localeuidoupc': '201', 'status': True, 'class': 'chn'})[-1].text
                        m_list.append([4, chn_def])
            else:
                def_bi_lng = present_part.find(
                    'span', attrs={'class': 'def-g'})

                if def_bi_lng:
                    chn_def = def_bi_lng.findAll(
                        'span', attrs={'localeuidoupc': '201', 'status': True, 'class': 'chn'})[-1].text
                    m_list.append([4, chn_def])

        def get_part(m_list, present_part):
            part = present_part.find(
                'span', attrs={'class': 'pos', 'level': True, 'pos': True}).text
            m_list.append([2, part])

            classified_defs = present_part.findAll(
                'span', attrs={'level': '2', 'class': 'sd-g'})

            if classified_defs:
                # 如果def有分类
                for def_class in classified_defs:
                    class_name = def_class.find(
                        'span', attrs={'class': 'sd'}).findChildren()[0].text
                    m_list.append([3, class_name])
                    get_def_list(m_list, def_class)
            else:
                # 如果def没有分类
                get_def_list(m_list, present_part)
            # 变形
            get_dr(m_list, present_part)

        def wrap_structure(m):
            '''将提取的结构包装为html'''
            temp = 0
            my_str = ''

            for flag in m:
                if flag[0] > temp:
                    while (flag[0] > temp):
                        my_str += '<ul><li>'
                        temp += 1
                    my_str += flag[1]
                elif flag[0] == temp:
                    my_str += '</li><li>'
                    my_str += flag[1]
                elif flag[0] < temp:
                    while(temp > flag[0]):
                        my_str += '</li></ul>'
                        temp -= 1
                    my_str += '</li><li>'
                    my_str += flag[1]
            while(temp > 0):
                my_str += '</li></ul>'
                temp -= 1
                # for i_tuple in m:
                #    i_tuple=list(i_tuple)
                # i_str = ''.join(i_tuple)
                # my_str = my_str + '<li>' + i_str + '</li>'
                # my_str='<ul><li>'+''.join(m[0])+'<ul>'+''.join(m[1])+':'+''.join(m[2])+'</ul></li></ul>'
                return my_str

        def simple_wrap(m_list):
            if not m_list:
                return ''
            my_str = '<p>'
            for ele in m_list:
                my_str += (ele[0]-1)*2*'&nbsp;'+ele[1]
                my_str += '<br>'
            my_str += '</p>'
            return my_str

        def extract_def(soup):
            m = []
            entry_list = soup.findAll('span', attrs={'class': 'entry'})
            if entry_list:
                for entry in entry_list:
                    # 一个索引多个词条
                    title = entry.find(
                        'span', attrs={'class': 'h', 'level': '3'}).text
                    '''检查查询单词是否等于词头'''
                    # flag = False
                    # if m:
                    #     if m[0][1].lower() != title.lower():
                    #         for m_member in m:
                    #             if m_member[0] == 4:
                    #                 flag = True
                    #                 break
                    # if flag:
                    #     break
                    m.append([1, title])

                    part_of_speech_list = []
                    temp = entry.findAll(
                        'span', attrs={'topic': True, 'bookmark': True, 'fk': False, 'class': 'Ref'})
                    if temp:
                        # 如果有多个词性
                        for x in temp:
                            part_of_speech_list.append(x.get('bookmark'))
                        for part_of_speech in part_of_speech_list:
                            present_part = entry.find(
                                'span', attrs={'id': part_of_speech})
                            if not present_part:
                                part_of_speech_text = entry.find(
                                    'span', attrs={'topic': True, 'bookmark': True, 'fk': False, 'class': 'Ref'}).text
                                m.append([2, part_of_speech_text])
                                present_part = entry
                                get_def_list(m, present_part)
                                continue
                            get_part(m, present_part)

                    elif not entry.find('span', attrs={'class': 'pos', 'level': True, 'pos': True}):
                        continue
                    else:
                        # 仅有单个词性
                        get_part(m, entry)
            else:
                # 如果找不到则按照短语词条处理
                get_phrase_def(m, soup)
            return simple_wrap(m)

        my_str = extract_def(soup)
        if my_str:
            return my_str
        else:
            return ''

    @with_styles(cssfile='_oald8.css')
    def _css(self, val):
        return val
