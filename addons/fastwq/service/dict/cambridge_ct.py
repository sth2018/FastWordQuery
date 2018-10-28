#-*- coding:utf-8 -*-
from ..base import *
from .cambridge import Cambridge

@register([u'剑桥词典-英汉繁', u'Cambridge(英汉繁)'])
class CambridgeCT(Cambridge):

    def __init__(self):
        super(CambridgeCT, self).__init__()

    def _get_url(self):
        return u'https://dictionary.cambridge.org/us/dictionary/english-chinese-traditional/'
