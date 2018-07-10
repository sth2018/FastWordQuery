#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 sthoo <sth201807@gmail.com>
#
# Support: Report an issue at https://github.com/sth2018/FastWordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from anki.lang import currentLang


__all__ = ['_', '_cl', '_sl']


#Language Define, [Key, zh_CN, en]
arr = [
    ['CHECK_FILENAME_LABEL', u'使用文件名作为标签', u'Use Filename As Label'],
    ['EXPORT_MEDIA', u'导出媒体文件', u'Export Media Files'],
    ['DICTS_FOLDERS', u'字典文件夹', u'Dictionary Folder'],
    ['CHOOSE_NOTE_TYPES', u'选择笔记类型', u'Choose Note Type'],
    ['CURRENT_NOTE_TYPE', u'当前类型', u'Current type'],
    ['MDX_SERVER', u'MDX服务器', u'MDX server'],
    ['USE_DICTIONARY', u'使用字典', u'Use dict'],
    ['UPDATED', u'更新', u'Updated'],
    ['CARDS', u'卡片', u'Cards'],
    ['FAILURE', u'失败', u'Failure'],
    ['SUCCESS', u'成功', u'Success'],
    ['QUERIED', u'查询', u'Queried'],
    ['FIELDS', u'字段', u'Fields'],
    ['WORDS', u'单词', u'Words'],
    ['NOT_DICT_FIELD', u'忽略', u'Ignore'],   #不是字典字段
    ['NOTE_TYPE_FIELDS', u'<b>笔记字段</b>', u'<b>Note fields</b>'],
    ['DICTS', u'<b>字典</b>', u'<b>Dictionary</b>'],
    ['DICT_FIELDS', u'<b>字典字段</b>', u'<b>Fields</b>'],
    ['RADIOS_DESC', u'<b>单选框选中为待查询单词字段</b>', u'<b>Word field needs to be selected.</b>'],
    ['NO_QUERY_WORD', u'查询字段无单词', u'No word is found in the query field'],
    ['CSS_NOT_FOUND', u'没有找到CSS文件，请手动选择', u'No valid css stylesheets found, please choose the file'],
    ['ABOUT', u'关于', u'About'],
    ['REPOSITORY', u'项目地址', u'Project Repo'],
    ['FEEDBACK', u'反馈', u'Feedback'],
    ['VERSION', u'版本', u'Version'],
    ['LATEST_VERSION', u'已经是最新版本.', u'It\'s the lastest version.'],
    ['ABNORMAL_VERSION', u'当前版本异常.', u'The current version is abnormal.'],
    ['CHECK_FAILURE', u'版本检查失败.', u'Version check failure.'],
    ['NEW_VERSION', u'检查到新版本:', u'New version:'],
    ['UPDATE', u'更新', u'Update'],
    ['FORCE_UPDATE', u'强制更新字段', u'Force Update Fields'],
    ['SETTINGS', u'参数', u'Settings'],
    ['THREAD_NUMBER', u'线程数', u'Thread Number'],
    ['INITLIZING_DICT', u'初始化词典...', u'Initlizing Dictionary...'],

    ['BRE_PRON', u'英式发音', u'British Pronunciation'],
    ['AME_PRON', u'美式发音', u'American Pronunciation'],
    ['PRON', u'发音', u'Pronunciation'],
    ['EXAMPLE', u'例句', u'Example'],
    ['TRANS', u'翻译', u'Translation'],
    ['DEF', u'释义', u'Definition'],
    ['PHON', u'音标', u'Phonetic'],
    ['BRE_PHON', u'英式音标', u'British Phonetic'],
    ['AME_PHON', u'美式音标', u'American Phonetic'],
    ['IMAGE', u'图片', u'Image'],
]

trans = {item[0]: {'zh_CN': item[1], 'en': item[2]} for item in arr}

def _(key, lang=currentLang):
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'

    def disp(s):
        return s.lower().capitalize()
    
    if key not in trans or lang not in trans[key]:
        return disp(key)
    return trans[key][lang]


def _cl(labels, lang=currentLang):
    if isinstance(labels, basestring):
        return _(labels)
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'
    return labels[0] if lang == 'zh_CN' else labels[1]


def _sl(key):
    return trans[key].values()
