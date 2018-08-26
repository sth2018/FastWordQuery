#-*- coding:utf-8 -*-
import os
try:
    import urllib2
except:
    import urllib.request as urllib2
import json
from aqt.utils import showInfo
from ..base import WebService, export, register, with_styles

oxford_download_mp3 = True

@register(u'Oxford')
class Oxford(WebService):

    def __init__(self):
        super(Oxford, self).__init__()

    def _get_from_api(self, lang='en'):
        app_id = '45aecf84'
        app_key = 'bb36fd6a1259e5baf8df6110a2f7fc8f'
        headers = {'app_id': app_id, 'app_key': app_key}
        word_id = urllib2.quote(self.word.lower().replace(' ', '_'))
        url = u'https://od-api.oxforddictionaries.com/api/v1/entries/' + lang + u'/' + word_id
        result = {'lexicalEntries': ''}
        try:
            result.update(json.loads(self.get_response(url, headers=headers, timeout=10))['results'][0])
        except:
            pass
        return self.cache_this(result)

    @export('DEF')
    def fld_definition(self):
        try:
            return self._get_field('lexicalEntries')[0]['entries'][0]['senses'][0]['definitions'][0]
        except:
            return ''

    def _fld_pron_mp3(self, audio_url):
        if oxford_download_mp3 and audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('PRON')
    def fld_pron(self):
        try:
            entries = self._get_field('lexicalEntries')
            prons_mp3 = ''
            for entry in entries:
                if 'pronunciations' in entry:
                    prons = entry['pronunciations']
                    pos = entry['lexicalCategory']
                    prons_mp3 += '<br>' if prons_mp3 else '' + u'<br>'.join(
                        u'{0}({1}) {2}'.format(
                            pron['dialects'][0] + ' ' if 'dialects' in pron else '',
                            pos,
                            self._fld_pron_mp3(pron['audioFile'])) for pron in prons)
            return prons_mp3
        except:
            return ''

    @export('PHON')
    def fld_phon(self):
        try:
            prons = self._get_field('lexicalEntries')[0]['pronunciations']
            return u'<br>'.join(u'{0}{1}'.format(pron['dialects'][0] + ': ' if 'dialects' in pron else '', pron['phoneticSpelling']) for pron in prons)
        except:
            return ''

    @export('EXAMPLE')
    def fld_example(self):
        try:
            entries = self._get_field('lexicalEntries')[0]['entries'][0]['senses'][0]['examples']
            return u'<br>'.join(entry['text'] for entry in entries)
        except:
            return ''

    @export([u'派生词', u'Derivatives'])
    def fld_deriv(self):
        try:
            entries = self._get_field('lexicalEntries')[0]['derivatives']
            return u', '.join(entry['text'] for entry in entries)
        except:
            return ''

    @export([u'词性', u'POS'])
    def fld_pos(self):
        try:
            entries = self._get_field('lexicalEntries')
            return u', '.join(entry['lexicalCategory'] for entry in entries)
        except:
            return ''
