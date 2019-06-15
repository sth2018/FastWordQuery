# -*- coding:utf-8 -*-
#
# Copyright (C) 2018 sthoo <sth201807@gmail.com>
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

try:
    basestring
except NameError:
    basestring = str

__all__ = ['_', '_cl', '_sl']

# Language Define, [Key, zh_CN, en]
_arr = [
    ['CHECK_FILENAME_LABEL', u'使用文件名作为标签', u'Use the Filename as Label'],
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
    ['NOT_DICT_FIELD', u'忽略', u'Ignore'],  # 不是字典字段
    ['NOTE_TYPE_FIELDS', u'<b>笔记字段</b>', u'<b>Note Fields</b>'],
    ['DICTS', u'<b>字典</b>', u'<b>Dictionary</b>'],
    ['DICT_FIELDS', u'<b>字典字段</b>', u'<b>Fields</b>'],
    [
        'RADIOS_DESC', u'<b>单选框选中为待查询单词字段</b>',
        u'<b> Select the field to be queried with single selection.</b>'
    ],
    ['NO_QUERY_WORD', u'查询字段无单词', u'The query field is empty'],
    [
        'CSS_NOT_FOUND', u'没有找到CSS文件，请手动选择',
        u'No CSS file found, please select one manually.'
    ],
    ['ABOUT', u'关于', u'About'],
    ['REPOSITORY', u'项目地址', u'Project Repo'],
    ['FEEDBACK', u'反馈', u'Feedback'],
    ['VERSION', u'版本', u'Current Version'],
    ['LATEST_VERSION', u'已经是最新版本.', u'You are using the lastest version.'],
    ['ABNORMAL_VERSION', u'当前版本异常.', u'The current version is abnormal.'],
    ['CHECK_FAILURE', u'版本检查失败.', u'Version check failed.'],
    ['NEW_VERSION', u'检查到新版本:', u'New version available:'],
    ['UPDATE', u'更新', u'Update'],
    ['AUTO_UPDATE', u'自动检测新版本', u'Auto check new version'],
    ['CHECK_UPDATE', u'检测更新', u'Check Update'],
    [
        'IGNORE_MDX_WORDCASE', u'忽略本地词典单词大小写',
        u'Ignore MDX dictionary word case'
    ],
    ['FORCE_UPDATE', u'强制更新字段', u'Forced Updates of all fields'],
    ['IGNORE_ACCENTS', u'忽略声调', u'Ignore Accents'],
    ['SKIP_VALUED', u'跳过有值项', u'Skip non-empty'],
    ['SKIPED', u'略过', 'Skipped'],
    ['SETTINGS', u'参数', u'Settings'],
    ['THREAD_NUMBER', u'线程数', u'Number of Threads'],
    ['INITLIZING_DICT', u'初始化词典...', u'Initlizing Dictionary...'],
    [
        'PLS_SET_DICTIONARY_FIELDS', u'请设置字典和字段',
        u'Please set the dictionary and fields.'
    ],
    ['CONFIG_INDEX', u'配置 %s', u'Config %s'],
    ['SELECT_ALL', u'全选', u'All'],
    ['DICTS_NAME', u'字典名称', u'Dictionary Name'],
    ['EDIT', u'编辑', u'Edit'],
    ['QUERY', u'查询', u'Query'],
    ['QUERY_SELECTED', u'查询选中项', u'Query Selected'],
    ['ALL_FIELDS', u'所有字段', u'All Fields'],
    ['CURRENT_FIELDS', u'当前字段', u'Current Fields'],
    ['OPTIONS', u'选项', u'Options'],
    ['CLOZE_WORD', u'单词填空', u'Cloze word'],
    ['CLOZE_WORD_FORMAT', '单词填空格式', 'Cloze word formater'],
    ['SOUND_FORMAT', '发音格式化', 'Sound formater'],
    ['BRE_PRON', u'英式发音', u'British Pronunciation'],
    ['AME_PRON', u'美式发音', u'American Pronunciation'],
    ['PRON', u'发音', u'Audio Pronunciation'],
    ['EXAMPLE', u'例句', u'Examples'],
    ['TRANS', u'翻译', u'Translation'],
    ['DEF', u'释义', u'Definition'],
    ['PHON', u'音标', u'Phonetic Symbols'],
    ['BRE_PHON', u'英式音标', u'Phonetic Symbols (UK)'],
    ['BRE_PHON_NO_PREFIX', u'英式音标无前缀', u'Phonetic Symbols (UK) no prefix'],
    ['AME_PHON', u'美式音标', u'Phonetic Symbols (US)'],
    ['AME_PHON_NO_PREFIX', u'美式音标无前缀', u'Phonetic Symbols (US) no prefix'],
    ['IMAGE', u'图片', u'Images'],
]

_trans = {item[0]: {'zh_CN': item[1], 'en': item[2]} for item in _arr}


def _(key, lang=currentLang):
    '''get local language string'''
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'

    def disp(s):
        return s.lower().capitalize()

    if key not in _trans or lang not in _trans[key]:
        return disp(key)
    return _trans[key][lang]


def _cl(labels, lang=currentLang):
    '''get local language string from labels'''
    if isinstance(labels, basestring):
        return _(labels)
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'
    return labels[0] if lang == 'zh_CN' else labels[1]


def _sl(key):
    return _trans[key].values()
