#!/usr/bin/python
from os import environ as env
from sys import platform
import importlib
from tkinter import *
from functools import partial


class ResolveAutomation:
    def __init__(self):
        global dvr
        self.errorMessages = []
        self.resolve = None
        self.window = Tk()
        self.selectedProject = ''

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
            self.__startGUI()

    def __startGUI(self):
        self.__basigGUIsetup()
        self.btnsProjects = []

        projects = self.__getProjectsList()
        framePrjSelect = Frame(self.window, height=150, width=800)
        framePrjSelect.pack(fill=X)
        framePrjButtons = Frame(framePrjSelect, height=50, width=800)
        framePrjButtons.pack(side=BOTTOM)
        if len(projects) <= 9:
            prjLabel = Label(framePrjSelect, text='Select the project containing the sources:')
            prjLabel.pack(side=TOP, anchor=N)
            for index, prjName in enumerate(projects):
                button = Button(framePrjButtons, text=prjName,
                                command=partial(lambda i=index, prj=prjName: self.__onProjectSelect(i, prj)))
                button.pack(side=LEFT)
                self.btnsProjects.append(button)
            print(self.btnsProjects)
        else:
            # TODO: Implement input
            prjLabel = Label(framePrjSelect, text='Too many projects to list. Write the name here:')
            # a1 = Entry(window).place(x=80, y=50)

        frame2 = Frame(self.window, height=50, width=800, relief=RAISED, bg='white')
        frame2.pack(fill=X)

        self.window.mainloop()

    def __basigGUIsetup(self):
        self.window.title('DaVinci Resolve Automated Render')
        self.window.geometry('800x500')

    def __getProjectsList(self) -> [str]:
        pm = self.resolve.GetProjectManager()
        prjlist = pm.GetProjectListInCurrentFolder()
        return prjlist

    def __onProjectSelect(self, index: int, prjName: str):
        for btn in self.btnsProjects:
            btn['state'] = 'normal'
        self.btnsProjects[index]['state'] = 'disabled'
        self.selectedProject = prjName
        pass


if __name__ == '__main__':
    env.update({'RESOLVE_SCRIPT_API':
                '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting'})
    env.update({'RESOLVE_SCRIPT_LIB':
                '/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so'})
    env.update({'PYTHONPATH': '$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/'})

    buildVideos = ResolveAutomation()
else:
    print('This is an application. It can\'t be imported as a module')
