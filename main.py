#!/usr/bin/python
from os import environ as env
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from functools import partial

from davinci import DaVinciResolve


class ResolveAutomation:
    def __init__(self):
        """
        Initialize variables and load DaVinci scripting support
        """
        self.window = Tk()
        self.resolve = DaVinciResolve()
        self.outputPath = None

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
        self.frameClipsInfo.pack(padx=5, pady=10)
        self.frameProcessFolder = Frame(self.window, height=200, width=750)
        self.frameProcessFolder.pack(pady=10)

    def __generateProjectSelectionButtons(self) -> None:
        """
        Load the project list from Resolve and generate selection buttons
        """
        self.btnsProjects = []

        projects = self.resolve.getProjects()

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
        self.__cleanupWindowOnProjectChange()
        self.__generateBinSelectionButtons(self.resolve.loadProject(prjName))

    def __generateBinSelectionButtons(self, projectSelected) -> None:
        """
        Read folders from project root and generate selection buttons
        """
        if projectSelected:
            self.btnsFolders = []
            self.firstLevelFolders = self.resolve.getRootFolders()

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
        self.selectedFolder = self.resolve.setCurrentFolder(folder)
        self.__cleanupWindowOnFolderChange()
        self.__getFolderContents()

    def __getFolderContents(self) -> None:
        """
        Read folder contents and separate media into audio, video and timelines
        """
        self.clipsInFolder = self.resolve.getFolderContent()

        stats = Label(self.frameClipsInfo,
                      text=f'Folder contains: '
                           f'{len(self.clipsInFolder["audioClips"])} audio file(s), '
                           f'{len(self.clipsInFolder["videoClips"])} video file(s) and '
                           f'{len(self.clipsInFolder["timelines"])} timeline(s)')
        stats.pack(side=TOP, anchor=N)

        ouputFolderLabel = Label(self.frameClipsInfo, text='Select output folder:')
        ouputFolderLabel.pack(side=LEFT)
        outputFolderPath = Entry(self.frameClipsInfo, textvariable=self.outputPath)
        outputFolderPath.pack(side=LEFT)

        def __browseOutputFolder():
            self.outputPath = filedialog.askdirectory()
            outputFolderPath.delete(0, END)
            outputFolderPath.insert(0, self.outputPath)

        outputFolderBrowse = Button(self.frameClipsInfo, text='Browse', command=__browseOutputFolder)
        outputFolderBrowse.pack(side=LEFT)

        if len(self.clipsInFolder["videoClips"]) == 1 and len(self.clipsInFolder["audioClips"]) >= 1:
            self.__showProcessButton()

    def __showProcessButton(self) -> None:
        self.buttonProcess = Button(self.frameProcessFolder, text='START', command=self.__startProcessing)
        self.buttonProcess.pack(padx=5, pady=15, side=RIGHT)
        self.buttonStop = Button(self.frameProcessFolder, text='Cancel', command=self.__cancelProcessing)
        self.buttonStop.pack(padx=5, pady=15, side=RIGHT)
        self.buttonStop['state'] = 'disabled'
        pass

    def __startProcessing(self):
        self.buttonProcess['state'] = 'disabled'
        self.buttonStop['state'] = 'normal'
        self.window.poll = True
        self.__processFolder()

    def __cancelProcessing(self):
        self.window.poll = False
        self.buttonProcess['state'] = 'normal'
        self.buttonStop['state'] = 'disabled'

    def __processFolder(self):
        if self.window.poll:
            if len(self.clipsInFolder["audioClips"]):
                pass
            # print(f'processing...')
            # self.window.after(1000, self.__processFolder)

    def __cleanupWindowOnProjectChange(self):
        """
        Remove all generated buttons on project change
        """
        if self.frameFolderSelect.winfo_children():
            for w in self.frameFolderSelect.winfo_children():
                w.destroy()

        self.__cleanupWindowOnFolderChange()

    def __cleanupWindowOnFolderChange(self):
        """
        Remove process-specific buttons on folder change
        """
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
