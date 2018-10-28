#-*- coding:utf-8 -*-
from ..base import *
from .cambridge import Cambridge

@register([u'剑桥词典-英英', u'Cambridge(English)'])
class CambridgeEE(Cambridge):

    def __init__(self):
        super(CambridgeEE, self).__init__()

    def _get_url(self):
        return u'https://dictionary.cambridge.org/dictionary/english/'
