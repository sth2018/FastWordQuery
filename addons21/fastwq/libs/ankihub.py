try:
    import httplib
except:
    import http.client as httplib
try:
    import urllib2
except:
    import urllib.request as urllib2
import json
import os
import sys
import zipfile
import traceback
import io
import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from anki.hooks import addHook
from anki.utils import isMac, isWin
from ..context import APP_ICON
from .AnkiHub.updates import Ui_DialogUpdates
from .AnkiHub.markdown2 import markdown


__all__ = ['update']


# taken from Anki's aqt/profiles.py
def defaultBase():
    path = mw.pm.addonFolder()
    return os.path.dirname(os.path.abspath(path))


headers = {"User-Agent": "AnkiHub"}
dataPath = os.path.join(defaultBase(),'.fastwq_2.1.x_ankihub.json')


class DialogUpdates(QDialog, Ui_DialogUpdates):

    def __init__(self, parent, data, oldData, callback):
        parent = parent if parent else mw
        QDialog.__init__(self, parent)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        self.setWindowIcon(APP_ICON)
        self.setupUi(self)
        totalSize = sum(map(lambda x:x['size'],data['assets']))
        def answer():
            self.update.setEnabled(False)
            callback(self.appendHtml, self.finish)

        self.html = u''
        self.appendHtml(markdown(data['body']))

        #if not automaticAnswer:
        self.update.clicked.connect(lambda:answer())

        fromVersion = ''
        if 'tag_name' in oldData:
            fromVersion = u'from {0} '.format(oldData['tag_name'])
        self.labelUpdates.setText(
            str(self.labelUpdates.text()).format(
                data['name'],
                fromVersion,
                data['tag_name']))

    def appendHtml(self,html='',temp=''):
        self.html += html
        self.textBrowser.setHtml(u'<html><body>{0}{1}{2}</body></html>'.format(self.html, temp, u'<div id="text_bottom"></div>'))
        self.textBrowser.scrollToAnchor('text_bottom') 

    def finish(self):
        self.hide()
        self.destroy()
        showInfo('Updated. Please restart Anki.')
        pass


def installZipFile(data, fname):
    base = os.path.join(mw.pm.addonFolder(), 'fastwq')
    if fname.endswith(".py"):
        path = os.path.join(base, fname)
        with open(path, "wb") as file:
            file.write(data)
            file.close()
        return True
    # .zip file
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipfile:
        return False
    for n in z.namelist():
        if n.endswith("/"):
            # folder; ignore
            continue
        # write
        z.extract(n, base)
    return True


def asset(a):
    return {
        'url': a['browser_download_url'],
        'size': a['size']
    }


def updateSingle(repositories, path, data):
    def callback(appendHtml, onReady):
        for asset in data['assets']:
            code = asset['url']
            p, fname = os.path.split(code)
            appendHtml(temp='<br />Downloading {1}: {0}%<br/>'.format(0,fname))
            try:
                urlthread = UrlThread(code)
                urlthread.start()
                urlthread.join()
                response = urlthread.response#urllib2.urlopen(code)
                meta = response.info()
                file_size = int(meta.get("Content-Length"))
            except:
                appendHtml('Downloading file error!<br/>')
                return
            d = b''
            dl = 0
            i = 0
            lastPercent = None
            while True:
                dkb = response.read(1024)
                if not dkb:
                    break
                dl += len(dkb)
                d += dkb
                if dl*100/file_size>i:
                    lastPercent = int(dl*100/file_size)
                    i = lastPercent+1
                    appendHtml(temp='<br />Downloading {1}: {0}%<br/>'.format(lastPercent,fname))
                QApplication.instance().processEvents()
            appendHtml('<br />Downloading {1}: 100%<br/>'.format(int(dl*100/file_size),fname))
            appendHtml('Installing ...<br/>')
            if not installZipFile(d, fname):
                appendHtml('Corrupt file<br/>')
            else:
                repositories[path] = data
                repositories[path]['update'] = 'ask'
                with open(dataPath,'w') as f:
                    json.dump(repositories,f,indent=2)
                    f.close()
                appendHtml('Done.<br/>')
                onReady() # close the AnkiHub update window

    return callback


def update(add=[], VERSION='v0.0.0', background=False):
    # progress win
    if not background:
        progresswin = QProgressDialog('Update Checking...', '', 0, 0, mw)
        progresswin.setWindowModality(Qt.ApplicationModal)
        progresswin.setCancelButton(None)
        progresswin.setWindowFlags(
            progresswin.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        progresswin.setWindowTitle('FastWQ - Updater')
        progresswin.setWindowIcon(APP_ICON)
        progresswin.resize(280, 60)
        progresswin.show()
    else:
        progresswin = None
    #
    conn = httplib.HTTPSConnection("api.github.com")
    try:
        with open(dataPath,'r') as f:
            repositories = json.load(f)
            f.close()
    except:
        repositories = {}
        
    for a in add:
        if a not in repositories:
            repositories[a] = {
                'id': 0,
                'update': 'ask'
            }

    for path,repository in repositories.items():
        username,repositoryName = path.split('/')
        try:
            urlthread = UrlThread("https://api.github.com/repos/{0}/releases/latest".format(path))
            urlthread.start()
            urlthread.join()
            release = json.loads(urlthread.response.read())
        except Exception as e:
            release = {}

        if 'id' in release:
            if release['id'] != repository['id']:
                data = {
                    'id': release['id'],
                    'name': repositoryName,
                    'tag_name': release['tag_name'],
                    'body': '### {0}\n'.format(release['name']) + release['body'],
                    'assets': [asset(release['assets'][1])],
                    'update': 'ask'
                }
                if 'tag_name' in repository:
                    oldVersion = map(int,repository['tag_name'][1:].split('.'))
                    oldVersion = [x for x in oldVersion]
                    while len(oldVersion)<3:
                        oldVersion.append(0)
                else:
                    oldVersion = map(int,VERSION[1:].split('.'))#[0,0,0]
                    oldVersion = [x for x in oldVersion]
                newVersion = map(int,data['tag_name'][1:].split('.'))
                newVersion = [x for x in newVersion]
                isMinor = len(newVersion)>2 and newVersion[2]>0
                while len(newVersion)<3:
                    newVersion.append(0)
                i = oldVersion[2]+1
                if oldVersion[0]<newVersion[0] or oldVersion[1]<newVersion[1]:
                    if isMinor:
                        i = 1
                while i<newVersion[2]:
                    if progresswin and progresswin.wasCanceled():
                        break
                    try:
                        minorTagName = 'v{0}.{1}.{2}'.format(newVersion[0],oldVersion[1],i)
                        urlthread = UrlThread("https://api.github.com/repos/{0}/releases/tags/{1}".format(path,minorTagName))
                        urlthread.start()
                        urlthread.join()
                        responseData = urlthread.response.read()
                        minor = json.loads(responseData)
                        data['body'] += '\n\n### {0}\n'.format(minor['name']) + minor['body']
                    except:
                        pass
                    i += 1
                if oldVersion[0]<newVersion[0] or oldVersion[1]<newVersion[1]:
                    # new major release necessary!
                    # if the newest version is minor, fetch the additional assets from the major
                    if isMinor and (background or not progresswin.wasCanceled()): 
                        try:
                            majorTagName = 'v{0}.{1}'.format(newVersion[0],newVersion[1])
                            urlthread = UrlThread(
                                "https://api.github.com/repos/{0}/releases/tags/{1}".format(path,majorTagName),
                                "https://api.github.com/repos/{0}/releases/tags/{1}.0".format(path,majorTagName)
                            )
                            urlthread.start()
                            urlthread.join()
                            responseData = urlthread.response.read()
                            major = json.loads(responseData)
                            data['body'] += '\n\n### {0}\n'.format(major['name']) + major['body']
                        except:
                            pass
                
                if background or not progresswin.wasCanceled():
                    if progresswin:
                        progresswin.hide()
                        progresswin.destroy()
                    dialog = DialogUpdates(None, data, repository, updateSingle(repositories, path, data))
                    dialog.exec_()
                    dialog.destroy()
                else:
                    if progresswin:
                        progresswin.hide()
                        progresswin.destroy()
                return 1
            else:
                if progresswin:
                    progresswin.hide()
                    progresswin.destroy()
                return 0
    if progresswin:
        progresswin.hide()
        progresswin.destroy()
    return -1


class UrlThread(QThread):

    def __init__(self, url, backurl=None):
        super(UrlThread, self).__init__()
        self.response = None
        self.url = url
        self.backurl = backurl
        self.finished = False
    
    def run(self):
        try:
            self.response = urllib2.urlopen(self.url)
        except:
            if self.backurl:
                try:
                    self.response = urllib2.urlopen(self.backurl)
                except:
                    pass
        self.finished = True

    def join(self):
        while not self.finished:
            QApplication.instance().processEvents()
            self.wait(30)
