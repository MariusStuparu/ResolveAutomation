#!/usr/bin/python
from os import environ as env
from sys import platform
import importlib
from tkinter import *
from functools import partial


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
        self.framePrjSelect.pack(fill=X, pady=15)
        self.frameFolderSelect = Frame(self.window, height=150, width=750, relief=SUNKEN)
        self.frameFolderSelect.pack(fill=X, pady=15)

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
        self.__generateBinSelectionButtons()

    def __generateBinSelectionButtons(self) -> None:
        if self.selectedProject:
            self.btnsFolders = []
            self.mediaPool = self.selectedProject.GetMediaPool()
            self.rootFolder = self.mediaPool.GetRootFolder()
            self.firstLevelFolders = self.rootFolder.GetSubFolderList()

            if self.frameFolderSelect.winfo_children():
                for w in self.frameFolderSelect.winfo_children():
                    w.destroy()

            selectFolderLabel = Label(self.frameFolderSelect, text='Select the folder to be processed:')
            selectFolderLabel.pack(side=TOP, anchor=N)

            for index, folder in enumerate(self.firstLevelFolders):
                folderName = folder.GetName()
                button = Button(self.frameFolderSelect, text=folderName,
                                command=partial(lambda i=index, prj=folder: self.__onFolderSelect(i, prj)))
                button.pack(side=LEFT, padx=10)
                self.btnsFolders.append(button)

    def __onFolderSelect(self, index: int, folder) -> None:
        for btn in self.btnsFolders:
            btn['state'] = 'normal'
        self.btnsFolders[index]['state'] = 'disabled'
        self.selectedFolder = self.mediaPool.SetCurrentFolder(folder)


if __name__ == '__main__':
    env.update({'RESOLVE_SCRIPT_API':
                '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting'})
    env.update({'RESOLVE_SCRIPT_LIB':
                '/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so'})
    env.update({'PYTHONPATH': '$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/'})

    buildVideos = ResolveAutomation()
else:
    print('This is an application. It can\'t be imported as a module')
