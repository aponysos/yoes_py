import re

headwords_pattern = re.compile('\A([\w\s&]+)\n+\Z')
findoutmore_pattern = re.compile('\A(\d+) -> (\d+) : (\d+)\n+\Z')

def ProcessHeadwordTxtLine(line):
    m = headwords_pattern.match(line)
    if m:
        headwords.append(m.group(1))

def ProcessFindoutmoreTxtLine(line):
    m = findoutmore_pattern.match(line)
    if m:
        findoutmore.append(m.groups())

import fileinput

headwords = []
findoutmore = []

def ProcessHeadwordTxtFile(filename):
    with fileinput.input(files=filename) as f:
        for line in f:
            ProcessHeadwordTxtLine(line)

def ProcessFindoutmoreTxtFile(filename):
    with fileinput.input(files=filename) as f:
        for line in f:
            ProcessFindoutmoreTxtLine(line)

ProcessHeadwordTxtFile('headwords.txt')
ProcessFindoutmoreTxtFile('findoutmore.txt')
#print(headwords)
#print(findoutmore)

import tkinter as tk

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        self.master.title('The Young Oxford Encyclopedia of Science')
        self.createWidgets()
        self.initWidgets()

    def createWidgets(self):
        self.btnQuit = tk.Button(self, text="Quit", command=self.quit)
        self.btnQuit.grid()
        self.lstHeadwords = tk.Listbox(self, 'highlightbackground')
        self.lstHeadwords.grid()
        self.lstHeadwords.bind('<<ListboxSelect>>', self.handlerClicked)
        self.lstFindoutmore = tk.Listbox(self)
        self.lstFindoutmore.grid()

    def initWidgets(self):
        for i, headword in enumerate(headwords):
            self.lstHeadwords.insert(i, headword)

    def handlerClicked(self, event):
        curselction = self.lstHeadwords.curselection()
        if curselction == ():
            return
        self.lstFindoutmore.delete(0, tk.END)
        for i, [fr, to, tp] in enumerate(findoutmore):
            if int(fr) == curselction[0]:
                self.lstFindoutmore.insert(tk.END, headwords[int(to)])
        

app = Application()
app.mainloop()