#-*- coding:utf-8 -*-
from ..base import *
from .cambridge import Cambridge

@register([u'剑桥词典-英汉简', u'Cambridge(英汉简)'])
class CambridgeCS(Cambridge):

    def __init__(self):
        super(CambridgeCS, self).__init__()

    def _get_url(self):
        return u'https://dictionary.cambridge.org/us/dictionary/english-chinese-simplified/'
