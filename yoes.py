"""yoes is short for "Young Oxford Encyclopedia of Science", which is a name of a book.
The book is organized into many HEADWORDS, which are referenced much by each other.
This script is to analyze the dependance relationship between the HEADWORDS and to find
a proper learning sequence.
"""

import re
import fileinput
import tkinter as tk
import logging
import sqlite3

LOGGING_FORMAT =        '[%(levelname)5s] %(asctime)s %(msecs)3d <%(process)d:%(thread)d:%(threadName)10s> ' + \
                        '{%(filename)s:%(lineno)4d%(funcName)30s} %(message)s'
LOGGING_DATE_FORMAT =   '%Y-%m-%d %H:%M:%S'
LOGGING_FILENAME =      'yoes.log'

logging.basicConfig(
    level=logging.DEBUG,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATE_FORMAT,
    filename=LOGGING_FILENAME,
    filemode='w')
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATE_FORMAT,
    filename=LOGGING_FILENAME,
    filemode='w')
logging.basicConfig(
    level=logging.ERROR,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATE_FORMAT,
    filename=LOGGING_FILENAME,
    filemode='w')

logging.info('Start logging ...')

HEADWORS_TXTFILE_LINE_PATTERN = re.compile(r'\A([\w\s&]+)\n+\Z')
FINDOUTMORE_TXTFILE_LINE_PATTERN = re.compile(r'\A(\d+) -> (\d+) : (\d+)\n+\Z')

HEADWORDS = list()
FINDOUTMORE = list()

def process_headwords_txtfile_line(line):
    """Get a headword from a line of string from headword.txt."""
    m = HEADWORS_TXTFILE_LINE_PATTERN.match(line)
    if m:
        HEADWORDS.append(m.group(1))

def process_findoutmore_txtfile_line(line):
    """Get a headword from a line of string from findoutmore.txt."""
    m = FINDOUTMORE_TXTFILE_LINE_PATTERN.match(line)
    if m:
        FINDOUTMORE.append(m.groups())

def process_headwords_txtfile(filename):
    """process headword.txt file line by line."""
    logging.debug('ENTER')
    logging.info('filename: %s', filename)
    with fileinput.input(files=filename) as f:
        for line in f:
            process_headwords_txtfile_line(line)
    logging.debug('LEAVE')

def process_findoutmore_txtfile(filename):
    """process findoutmore.txt file line by line."""
    logging.debug('ENTER')
    logging.info('filename: %s', filename)
    with fileinput.input(files=filename) as f:
        for line in f:
            process_findoutmore_txtfile_line(line)
    logging.debug('LEAVE')

def open_db():
    logging.debug('ENTER')
    conn = sqlite3.connect('yoes.db')
    logging.info('sqlite3.connect: %s', conn)
    conn.execute('''CREATE TABLE HEADWORDS(
        ID          INT     PRIMARY KEY NOT NULL,
        HEADWORD    TEXT                NOT NULL
        );''')
    logging.info('CREATE TABLE HEADWORDS')
    logging.debug('LEAVE')

class Application(tk.Frame):
    def __init__(self, master=None):
        logging.debug('ENTER')
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        self.master.title('The Young Oxford Encyclopedia of Science')
        self.create_widgets()
        self.init_widgets()
        logging.debug('LEAVE')

    def create_widgets(self):
        logging.debug('ENTER')
        self.btnQuit = tk.Button(self, text="Quit", command=self.quit)
        self.btnQuit.grid()
        self.lstHeadwords = tk.Listbox(self)
        self.lstHeadwords.grid()
        self.lstHeadwords.bind('<<ListboxSelect>>', self.handler_listbox_selected)
        self.lstFindoutmore = tk.Listbox(self)
        self.lstFindoutmore.grid()
        logging.debug('LEAVE')

    def init_widgets(self):
        logging.debug('ENTER')
        process_headwords_txtfile('headwords.txt')
        process_findoutmore_txtfile('findoutmore.txt')
        for i, headword in enumerate(HEADWORDS):
            self.lstHeadwords.insert(i, headword)
        open_db()
        logging.debug('LEAVE')

    def handler_listbox_selected(self, event):
        logging.debug('ENTER')
        curselection = self.lstHeadwords.curselection()
        logging.info('curselection: %s', curselection)
        if curselection == ():
            return
        self.lstFindoutmore.delete(0, tk.END)
        for i, [fr, to, tp] in enumerate(FINDOUTMORE):
            if int(fr) == curselection[0]:
                self.lstFindoutmore.insert(tk.END, HEADWORDS[int(to)])
        

app = Application()
app.mainloop()

logging.info('End logging ...')
