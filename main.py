#!/usr/bin/python
from os import environ as env
from sys import platform
import importlib
from tkinter import *
from functools import partial
import time


class ResolveAutomation:
    def __init__(self):
        """
        Initialize variables and load DaVinci scripting support
        """
        global dvr
        self.errorMessages = []
        self.window = Tk()
        # Resolve specific
        self.resolve = None
        self.pm = None
        self.mediaStorage = None
        self.selectedProject = None
        self.mediaPool = None
        self.rootFolder = None
        self.firstLevelFolders = None
        self.selectedFolder = None
        self.clipsInFolder = None

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
            self.__startGUI()

    def __startGUI(self) -> None:
        """
        Main GUI controller
        """
        self.__basigGUIsetup()
        self.__generateProjectSelectionButtons()
        self.window.mainloop()

    def __basigGUIsetup(self) -> None:
        """
        Generic window decoration and setup
        """
        self.window.title('DaVinci Resolve Automated Render')
        self.window.geometry('800x500')
        self.framePrjSelect = Frame(self.window, height=150, width=800)
        self.framePrjSelect.pack(pady=15)
        self.frameFolderSelect = Frame(self.window, height=150, width=750)
        self.frameFolderSelect.pack(pady=15)
        self.frameClipsInfo = Frame(self.window, height=50, width=750)
        self.frameClipsInfo.pack(pady=10)
        self.frameProcessFolder = Frame(self.window, height=200, width=750)
        self.frameProcessFolder.pack(pady=10)

    def __generateProjectSelectionButtons(self) -> None:
        """
        Load the project list from Resolve and generate selection buttons
        """
        self.btnsProjects = []

        projects = self.pm.GetProjectListInCurrentFolder()

        framePrjButtons = Frame(self.framePrjSelect, height=50, width=800)
        framePrjButtons.pack(side=BOTTOM, pady=5)
        if len(projects) <= 9:
            prjLabel = Label(self.framePrjSelect, text='Select your project:')
            prjLabel.pack(side=TOP, anchor=N)
            for index, prjName in enumerate(projects):
                button = Button(framePrjButtons, text=prjName,
                                command=partial(lambda i=index, prj=prjName: self.__onProjectSelect(i, prj)))
                button.pack(side=LEFT, padx=10)
                self.btnsProjects.append(button)
        else:
            # TODO: Implement input
            prjLabel = Label(self.framePrjSelect, text='Too many projects to list. Write the name here:')
            # a1 = Entry(window).place(x=80, y=50)

    def __onProjectSelect(self, index: int, prjName: str) -> None:
        """
        Action handler for project selection buttons
        :param index: position of the button inside the btnsProjects list
        :param prjName: string name of the project, as received from Resolve
        """
        for btn in self.btnsProjects:
            btn['state'] = 'normal'
        self.btnsProjects[index]['state'] = 'disabled'
        self.selectedProject = self.pm.LoadProject(prjName)
        self.__cleanupWindowOnProjectChange()
        self.__generateBinSelectionButtons()

    def __generateBinSelectionButtons(self) -> None:
        """
        Read folders from project root and generate selection buttons
        """
        if self.selectedProject:
            self.btnsFolders = []
            self.mediaPool = self.selectedProject.GetMediaPool()
            self.rootFolder = self.mediaPool.GetRootFolder()
            self.firstLevelFolders = self.rootFolder.GetSubFolderList()

            if len(self.firstLevelFolders):
                selectFolderLabel = Label(self.frameFolderSelect, text='Select the folder to be processed:')
                selectFolderLabel.pack(side=TOP, anchor=N)

                for index, folder in enumerate(self.firstLevelFolders):
                    folderName = folder.GetName()
                    button = Button(self.frameFolderSelect, text=folderName,
                                    command=partial(lambda i=index, prj=folder: self.__onFolderSelect(i, prj)))
                    button.pack(side=LEFT, padx=10)
                    self.btnsFolders.append(button)

    def __onFolderSelect(self, index: int, folder) -> None:
        """
        Action handler for folder selection buttons
        :param index: position of the button inside the btnsFolders list
        :param folder: string name of the folder, as received from Resolve
        """
        for btn in self.btnsFolders:
            btn['state'] = 'normal'
        self.btnsFolders[index]['state'] = 'disabled'
        self.mediaPool.SetCurrentFolder(folder)
        self.selectedFolder = self.mediaPool.GetCurrentFolder()
        self.__cleanupWindowOnFolderChange()
        self.__getFolderContents()

    def __getFolderContents(self) -> None:
        """
        Read folder contents and separate media into audio, video and timelines
        """
        self.clipsInFolder = self.selectedFolder.GetClips()
        self.audioFilesInFolder = []
        self.videoFilesInFolder = []
        self.timelinesInFolder = []

        for index in self.clipsInFolder:
            clip = self.clipsInFolder[index]
            if clip.GetClipProperty('Type') == 'Audio':
                self.audioFilesInFolder.append(clip)
            if clip.GetClipProperty('Type') == 'Video':
                self.videoFilesInFolder.append(clip)
            if clip.GetClipProperty('Type') == 'Timeline':
                self.timelinesInFolder.append(clip)

        stats = Label(self.frameClipsInfo,
                      text=f'Folder contains: '
                           f'{len(self.audioFilesInFolder)} audio file(s), '
                           f'{len(self.videoFilesInFolder)} video file(s) and '
                           f'{len(self.timelinesInFolder)} timeline(s)')
        stats.pack(side=TOP, anchor=N)
        if len(self.videoFilesInFolder) == 1 and len(self.audioFilesInFolder) >= 1:
            self.__showProcessButton()

    def __showProcessButton(self) -> None:
        self.processingEnabled = True
        self.buttonProcess = Button(self.frameProcessFolder, text='START', command=self.__processFolder)
        self.buttonProcess.pack(padx=5, pady=15, side=RIGHT)
        self.buttonStop = Button(self.frameProcessFolder, text='Cancel', command=self.__cancelProcessing)
        self.buttonStop.pack(padx=5, pady=15, side=RIGHT)
        self.buttonStop['state'] = 'disabled'
        pass

    def __processFolder(self):
        self.buttonProcess['state'] = 'disabled'
        self.buttonStop['state'] = 'normal'
        # for track in self.audioFilesInFolder:
        #     self.buttonProcess['state'] = 'disabled'
        #     self.buttonStop['state'] = 'normal'
        #     print(f'processing... {track}')
        #     time.sleep(5)
        # else:
        #     self.buttonProcess['state'] = 'normal'
        #     self.buttonStop['state'] = 'disabled'

    def __cancelProcessing(self):
        self.processingEnabled = False

    def __cleanupWindowOnProjectChange(self):
        if self.frameFolderSelect.winfo_children():
            for w in self.frameFolderSelect.winfo_children():
                w.destroy()

        if self.frameClipsInfo.winfo_children():
            for w in self.frameClipsInfo.winfo_children():
                w.destroy()

        if self.frameProcessFolder.winfo_children():
            for w in self.frameProcessFolder.winfo_children():
                w.destroy()

    def __cleanupWindowOnFolderChange(self):
        if self.frameClipsInfo.winfo_children():
            for w in self.frameClipsInfo.winfo_children():
                w.destroy()

        if self.frameProcessFolder.winfo_children():
            for w in self.frameProcessFolder.winfo_children():
                w.destroy()


if __name__ == '__main__':
    env.update({'RESOLVE_SCRIPT_API':
                '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting'})
    env.update({'RESOLVE_SCRIPT_LIB':
                '/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so'})
    env.update({'PYTHONPATH': '$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/'})

    buildVideos = ResolveAutomation()
else:
    print('This is an application. It can\'t be imported as a module')
