#!/usr/bin/python
from sys import platform
import importlib


class DaVinciResolve:
    def __init__(self, ):
        self.errorMessages = []

        self.resolve = None
        self.pm = None
        self.mediaStorage = None
        self.selectedProject = None
        self.mediaPool = None
        self.rootFolder = None
        self.selectedFolder = None

        try:
            import DaVinciResolveScript as dvr
        except ImportError:
            expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
            if platform.startswith("darwin"):
                expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
            elif platform.startswith("win") or platform.startswith("cygwin"):
                import os
                expectedPath = os.getenv(
                    'PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
            elif platform.startswith("linux"):
                expectedPath = "/opt/resolve/libs/Fusion/Modules/"
            try:
                self.dvr = importlib.import_module('DaVinciResolveScript', expectedPath + 'DaVinciResolveScript.py')
            except ImportError:
                self.errorMessages.append({
                    'type': 'missing required library',
                    'message': f'DaVinci Resolve library not found in {expectedPath}'
                })
        except AttributeError:
            self.errorMessages.append({
                'type': 'davinci_not_started',
                'message': 'DaVinci Resolve is not running. Make sure you start Resolve before running this app.'
            })
        finally:
            if dvr:
                self.resolve = dvr.scriptapp('Resolve')
            elif self.dvr:
                self.resolve = self.dvr.scriptapp('Resolve')
            self.pm = self.resolve.GetProjectManager()
            self.mediaStorage = self.resolve.GetMediaStorage()

    def getProjects(self):
        if self.pm:
            return self.pm.GetProjectListInCurrentFolder()
        else:
            return None

    def loadProject(self, projectName: str):
        if self.pm:
            self.selectedProject = self.pm.LoadProject(projectName)
            return self.selectedProject
        else:
            return None

    def getRootFolders(self):
        if self.selectedProject:
            self.mediaPool = self.selectedProject.GetMediaPool()
            self.rootFolder = self.mediaPool.GetRootFolder()
            return self.rootFolder.GetSubFolderList()
        else:
            return None

    def setCurrentFolder(self, folder):
        if self.mediaPool:
            self.mediaPool.SetCurrentFolder(folder)
            self.selectedFolder = folder
            return folder
        else:
            return None

    def getFolderContent(self):
        audioClips = []
        videoClips = []
        timelines = []
        clipsInFolder = self.selectedFolder.GetClips()

        for index in clipsInFolder:
            clip = clipsInFolder[index]
            if clip.GetClipProperty('Type') == 'Audio':
                audioClips.append(clip)
            if clip.GetClipProperty('Type') == 'Video':
                videoClips.append(clip)
            if clip.GetClipProperty('Type') == 'Timeline':
                timelines.append(clip)

        return {
            'audioClips': audioClips,
            'videoClips': videoClips,
            'timelines': timelines
        }


if __name__ == '__main__':
    pass
