#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 ST.Huang <wenhonghuang@gmail.com>
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


from .lang import _


VERSION = '1.0.0'


class Endpoint:
    repository = u' https://github.com/sth2018/FastWordQuery'
    feedback_issue = u'https://github.com/sth2018/FastWordQuery/issues'
    feedback_mail = u'wenhonghuang@gmail.com'
    check_version = u'https://raw.githubusercontent.com/sth2018/FastWordQuery/gh-pages/version'
    new_version = u' https://github.com/sth2018/FastWordQuery'
    user_guide = u'https://sth2018.github.io/FastWordQuery/'


class Template:
    tmpl_about = u'<b>{t0}</b><br />{version}<br /><b>{t1}</b><br /><a href="{url}">{url}</a><br /><b>{t2}</b><br /><a href="{feedback0}">{feedback0}</a><br /><a href="mailto:{feedback1}">{feedback1}</a>'.format(
        t0=_('VERSION'), version=VERSION, t1=_('REPOSITORY'), url=Endpoint.repository,
        t2=_('FEEDBACK'), feedback0=Endpoint.feedback_issue, feedback1=Endpoint.feedback_mail)
    new_version = u'{info} <a href="{url}">V{version}</a>'.format(
        info=_('NEW_VERSION'), url=Endpoint.new_version, version='{version}')
    latest_version = _('LATEST_VERSION')
    abnormal_version = _('ABNORMAL_VERSION')
    check_failure = u'{msg}'
    miss_css = u'MDX dictonary <b>{dict}</b> misses css file <b>{css}</b>. <br />Please choose the file.'
