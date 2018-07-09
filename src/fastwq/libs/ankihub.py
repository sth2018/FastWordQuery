from PyQt4 import QtCore,QtGui
import httplib
import urllib2
import json
import os
import sys
import zipfile
import traceback
import io
from AnkiHub.updates import Ui_DialogUpdates
from AnkiHub.markdown2 import markdown
import aqt
from aqt import mw
from anki.hooks import addHook
from anki.utils import isMac, isWin

'''
# taken from Anki's aqt/profiles.py
def defaultBase():
    print(mw.pm.addonFolder())
    if isWin:
        loc = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation)
        return os.path.join(loc, "Anki")
    elif isMac:
        return os.path.expanduser("~/Documents/Anki")
    else:
        p = os.path.expanduser("~/Anki")
        if os.path.exists(p):
            return p
        else:
            loc = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation)
            if loc[:-1] == QtGui.QDesktopServices.storageLocation(
                    QtGui.QDesktopServices.HomeLocation):
                return os.path.expanduser("~/Documents/Anki")
            else:
                return os.path.join(loc, "Anki")
'''

headers = {"User-Agent": "AnkiHub"}
dataPath = '.ankihub.json' #os.path.join(defaultBase(),'.ankihub.json')


class DialogUpdates(QtGui.QDialog, Ui_DialogUpdates):
    def __init__(self, parent, data, oldData, callback, automaticAnswer=None,install=False):
        QtGui.QDialog.__init__(self,parent)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~QtCore.Qt.WindowContextHelpButtonHint
        )
        self.setupUi(self)
        totalSize = sum(map(lambda x:x['size'],data['assets']))

        def answer(doUpdate,answ):
            self.update.setEnabled(False)
            #self.dont.setEnabled(False)
            #self.always.setEnabled(False)
            #self.never.setEnabled(False)
            callback(doUpdate,answ,self.appendHtml,self.finish,install)

        self.html = u''
        self.appendHtml(markdown(data['body']))

        #if not automaticAnswer:
        self.connect(self.update,QtCore.SIGNAL('clicked()'),
                        lambda:answer(True,'ask'))
            #self.connect(self.dont,QtCore.SIGNAL('clicked()'),
            #         lambda:answer(False,'ask'))
            #self.connect(self.always,QtCore.SIGNAL('clicked()'),
            #         lambda:answer(True,'always'))
            #self.connect(self.never,QtCore.SIGNAL('clicked()'),
            #         lambda:answer(False,'never'))
        #else:
            #self.update.setEnabled(False)
            #self.dont.setEnabled(False)
            #self.always.setEnabled(False)
            #self.never.setEnabled(False)
        #    answer(True,automaticAnswer)

        fromVersion = ''
        if 'tag_name' in oldData:
            fromVersion = u'from {0} '.format(oldData['tag_name'])
        self.labelUpdates.setText(
            unicode(self.labelUpdates.text()).format(
                data['name'],
                fromVersion,
                data['tag_name']))


    def appendHtml(self,html='',temp=''):
        self.html += html
        self.textBrowser.setHtml(u'<html><body>{0}{1}{2}</body></html>'.format(self.html, temp, u'<div id="text_bottom"></div>'))
        self.textBrowser.scrollToAnchor('text_bottom') 

    def finish(self):
        pass


def installZipFile(data, fname):
    base = mw.pm.addonFolder()#os.path.join(defaultBase(),'addons')
    if fname.endswith(".py"):
        path = os.path.join(base, fname)
        open(path, "wb").write(data)
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

profileLoaded = True
def _profileLoaded():
    profileLoaded = True

addHook("profileLoaded",_profileLoaded)

def updateSingle(repositories,path,data):
    def callback(doUpdate,answer,appendHtml,onReady,install):
        if doUpdate:
            for asset in data['assets']:
                code = asset['url']
                p, fname = os.path.split(code)
                response = urllib2.urlopen(code)
                meta = response.info()
                file_size = int(meta.getheaders("Content-Length")[0])
                d = buffer('')
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
                    QtGui.QApplication.instance().processEvents()
                appendHtml('<br />Downloading {1}: 100%<br/>'.format(int(dl*100/file_size),fname))
                def installData():
                    if install:
                        filesBefore = aqt.mw.addonManager.files()
                        #directoriesBefore = aqt.mw.addonManager.directories()
                    appendHtml('Installing ...<br/>')
                    if not installZipFile(d,fname):
                        appendHtml('Corrupt file<br/>')
                    else:
                        repositories[path] = data
                        repositories[path]['update'] = answer
                        with open(dataPath,'w') as file:
                            json.dump(repositories,file,indent=2)
                        if install:
                            appendHtml('Executing new scripts...<br/>')
                            newFiles = set(aqt.mw.addonManager.files()) - set(filesBefore)
                            #newDirectories = set(aqt.mw.addonManager.directories()) - set(directoriesBefore)
                            for file in newFiles:
                                try:
                                    __import__(file.replace(".py", ""))
                                except:
                                    traceback.print_exc()
                            #for directory in newDirectories:
                            #    try:
                            #        __import__(directory)
                            #    except:
                            #        traceback.print_exc()
                            aqt.mw.addonManager.rebuildAddonsMenu()
                            appendHtml('Done.<br/>')
                            onReady() # close the AnkiHub update window       
                        else:
                            appendHtml('Done.<br/>Please restart Anki.<br/>')
                            onReady() # close the AnkiHub update window
                        
                installData()
        else:
            repositories[path]['update'] = answer
            with open(dataPath,'w') as file:
                json.dump(repositories,file,indent=2)
            onReady()
    return callback

datas = []

def update(add=[],install=False, VERSION='v0.0.0'):
    conn = httplib.HTTPSConnection("api.github.com")
    try:
        with open(dataPath,'r') as file:
            repositories = json.load(file)
    except:
        repositories = {}
        #    'dayjaby/AnkiHub': {
        #        'id': 4089471,
        #        'update': 'ask'
        #    }
        #}
        
    for a in add:
        if a not in repositories:
            repositories[a] = {
                'id': 0,
                'update': 'ask'
            }

    ret = False
    for path,repository in repositories.items():
        username,repositoryName = path.split('/')
        if repository['update'] != 'never':
            try:
                url = "https://api.github.com/repos/{0}/releases/latest".format(path)
                responseData = urllib2.urlopen(url, timeout=10).read()
                release = json.loads(responseData)
                datas.append(responseData)
            except Exception as e:
                datas.append(e)
                release = {}

            if 'id' in release:
                if release['id'] != repository['id']:
                    data = {
                        'id': release['id'],
                        'name': repositoryName,
                        'tag_name': release['tag_name'],
                        'body': '### {0}\n'.format(release['name']) + release['body'],
                        'assets': map(asset,release['assets']),
                        'update': 'ask'
                    }
                    if 'tag_name' in repository:
                        oldVersion = map(int,repository['tag_name'][1:].split('.'))
                        while len(oldVersion)<3:
                            oldVersion.append(0)
                    else:
                        oldVersion = map(int,VERSION[1:].split('.'))#[0,0,0]
                    newVersion = map(int,data['tag_name'][1:].split('.'))
                    isMinor = len(newVersion)>2 and newVersion[2]>0
                    while len(newVersion)<3:
                        newVersion.append(0)
                    i = oldVersion[2]+1
                    if oldVersion[0]<newVersion[0] or oldVersion[1]<newVersion[1]:
                        if isMinor:
                            i = 1
                    while i<newVersion[2]:
                        try:
                            minorTagName = 'v{0}.{1}.{2}'.format(newVersion[0],oldVersion[1],i)
                            response = urllib2.urlopen("https://api.github.com/repos/{0}/releases/tags/{1}".format(path,minorTagName))
                            responseData = response.read()
                            minor = json.loads(responseData)
                            data['body'] += '\n\n### {0}\n'.format(minor['name']) + minor['body']
                            #data['assets'] += map(asset,minor['assets'])
                        except:
                            pass
                    
                        i += 1
                    if oldVersion[0]<newVersion[0] or oldVersion[1]<newVersion[1]:
                        # new major release necessary!
                        if isMinor: # if the newest version is minor, fetch the additional assets from the major
                            majorTagName = 'v{0}.{1}'.format(newVersion[0],newVersion[1])
                            try:
                                response = urllib2.urlopen("https://api.github.com/repos/{0}/releases/tags/{1}".format(path,majorTagName))
                            except:
                                response = urllib2.urlopen("https://api.github.com/repos/{0}/releases/tags/{1}.0".format(path,majorTagName))
                            responseData = response.read()
                            major = json.loads(responseData)
                            data['body'] += '\n\n### {0}\n'.format(major['name']) + major['body']
                            #data['assets'] += map(asset,major['assets'])
                        
                    if repository['update'] == 'always':
                        dialog = DialogUpdates(None,data,repository,updateSingle(repositories,path,data),'always')
                    elif install:
                        dialog = DialogUpdates(None,data,repository,updateSingle(repositories,path,data),'ask',install=True)
                    else:
                        dialog = DialogUpdates(None,data,repository,updateSingle(repositories,path,data))
                    dialog.exec_()
                    ret = True
    
    with open(dataPath,'w') as file:
        json.dump(repositories,file,indent=2)
    return ret

#update()

#def addRepository():
#    repo, ok = QtGui.QInputDialog.getText(aqt.mw,'Add GitHub repository',
#                                          'Path:',text='<name>/<repository>')
#    if repo and ok:
#        update([repo],install=True)
#
#firstAction = aqt.mw.form.menuPlugins.actions()[0]
#action = QtGui.QAction('From GitHub', aqt.mw)
#action.setIconVisibleInMenu(True)
#action.triggered.connect(addRepository)
#aqt.mw.form.menuPlugins.insertAction(firstAction,action)
