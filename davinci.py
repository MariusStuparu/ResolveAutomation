#!/usr/bin/python
from sys import platform
import importlib


class DaVinciResolve:
    def __init__(self, ):
        self.errorMessages = []
        self.RENDER_VIDEO_PRESET = 'H.265 Master'
        self.RENDER_AUDIO_PRESET = 'Audio Only'

        self.resolve = None
        self.pm = None
        self.mediaStorage = None
        self.selectedProject = None
        self.mediaPool = None
        self.rootFolder = None
        self.selectedFolder = None
        self.clipsInFolder = None
        self.workingAudioFile = None
        self.workingCompoundVideo = None
        self.workingTimeline = None
        self.finalTimeline = None

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

    def openPage(self, page: str):
        availablePages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
        if page in availablePages:
            self.resolve.OpenPage(page)

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
        compounds = []
        clipsInFolder = self.selectedFolder.GetClips()

        for index in clipsInFolder:
            clip = clipsInFolder[index]
            if clip.GetClipProperty('Type') == 'Audio':
                audioClips.append(clip)
            if clip.GetClipProperty('Type') == 'Video':
                videoClips.append(clip)
            if clip.GetClipProperty('Type') == 'Timeline':
                timelines.append(clip)
            if clip.GetClipProperty('Type') == 'Compound':
                compounds.append(clip)

        self.clipsInFolder = {
            'audioClips': audioClips,
            'videoClips': videoClips,
            'timelines': timelines,
            'compounds': []
        }

        return self.clipsInFolder

    def createTimelineFromAudio(self, audioClip):
        # self.__removeExistingAutomations()

        self.workingAudioFile = audioClip
        self.workingTimeline = self.mediaPool.CreateTimelineFromClips(f'Automated Timeline | {self.workingAudioFile.GetName()}', self.workingAudioFile)
        self.clipsInFolder['timelines'].append(self.workingTimeline)
        frameRate = self.selectedProject.GetSetting('timelineFrameRate')

        return {
            'timeline': self.workingTimeline,
            'duration': self.__getAudioDuration(self.workingTimeline),
            'framerate': frameRate
        }

    def addVideoClipToTimeline(self, videoClip, frames=None):
        if not frames:
            self.mediaPool.AppendToTimeline(videoClip)
        else:
            self.mediaPool.AppendToTimeline([{
                'mediaPoolItem': videoClip,
                'startFrame': 0,
                'endFrame': frames
            }])

    def createCompoundVideo(self):
        videoFiles = self.workingTimeline.GetItemListInTrack('video', 1)
        compound = self.workingTimeline.CreateCompoundClip(videoFiles, {
            'name': f'Compound Video | {self.workingAudioFile.GetName()}',
            'startTimecode': '00:00:00:00'
        })
        self.workingCompoundVideo = compound.GetMediaPoolItem()

    def createRenderJob(self, targetDir, renderVideoFileName, renderAudioFileName):
        """Render video and audio parts"""

        if self.selectedProject.DeleteAllRenderJobs():
            """Create render job for video part"""
            finalVideoTimeline = self.mediaPool.CreateTimelineFromClips(f'Automated Video | {renderVideoFileName}', self.workingCompoundVideo)
            self.selectedProject.SetCurrentTimeline(finalVideoTimeline)

            self.selectedProject.LoadRenderPreset(self.RENDER_VIDEO_PRESET)
            self.selectedProject.SetRenderSettings({
                'SelectAllFrames': True,
                'TargetDir': targetDir,
                'CustomName': renderVideoFileName,
                'ExportAudio': False,
                'ExportVideo': True
            })
            self.selectedProject.AddRenderJob()

            """Create render job for audio part"""
            finalAudioTimeline = self.mediaPool.CreateTimelineFromClips(f'Automated Audio | {renderAudioFileName}', self.workingAudioFile)
            self.selectedProject.SetCurrentTimeline(finalAudioTimeline)

            self.selectedProject.LoadRenderPreset(self.RENDER_AUDIO_PRESET)
            self.selectedProject.SetRenderSettings({
                'SelectAllFrames': True,
                'TargetDir': targetDir,
                'CustomName': renderAudioFileName,
                'ExportAudio': True,
                'ExportVideo': False
            })
            self.selectedProject.AddRenderJob()

            self.openPage('deliver')
            self.selectedProject.StartRendering()

    def checkIsRendering(self):
        return self.selectedProject.IsRenderingInProgress()

    def moveFinishedFileToRoot(self, clip):
        self.mediaPool.MoveClips([clip], self.rootFolder)

    def removeExistingAutomations(self):
        clipsInFolder = self.selectedFolder.GetClips()

        for index in clipsInFolder:
            clip = clipsInFolder[index]
            if clip.GetClipProperty('Type') == 'Timeline' or clip.GetClipProperty('Type') == 'Compound':
                self.mediaPool.DeleteClips(clip)

    def __getAudioDuration(self, timeline):
        audioTrack = timeline.GetItemListInTrack('audio', 1)
        audioTrackDuration = audioTrack[0].GetDuration()

        return audioTrackDuration


if __name__ == '__main__':
    pass
