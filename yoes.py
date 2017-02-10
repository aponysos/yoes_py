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

DB = sqlite3.connect('yoes.db')
logging.info('sqlite3.connect return: %s', DB)

def open_db():
    logging.debug('ENTER')
    DB.execute('''CREATE TABLE IF NOT EXISTS HEADWORDS(
        HEADWORD    TEXT    NOT NULL UNIQUE
        );''')
    logging.info('CREATE TABLE HEADWORDS')
    DB.execute('''CREATE TABLE IF NOT EXISTS FINDOUTMORE(
        HW          INT     NOT NULL,
        REF         INT     NOT NULL,
        TYPE        INT     DEFAULT(0),
        PRIMARY KEY(HW, REF)
        );''')
    logging.info('CREATE TABLE FINDOUTMORE')
    logging.debug('LEAVE')

def insert_headword(headword):
    logging.debug('ENTER: %s', headword)
    DB.execute('''INSERT OR REPLACE INTO HEADWORDS VALUES(?);''', headword)
    logging.info('headword added: %s', headword)
    logging.debug('LEAVE')

def insert_findoutmore(findoutmore):
    logging.debug('ENTER: %s', findoutmore)
    DB.execute('''INSERT OR REPLACE INTO FINDOUTMORE VALUES(?, ?, ?);''', findoutmore)
    logging.info('findoutmore added: %s', findoutmore)
    logging.debug('LEAVE')

def query_headwords():
    logging.debug('ENTER')
    cursor = DB.execute('''SELECT ROWID, HEADWORD FROM HEADWORDS;''')
    rows = cursor.fetchall()
    logging.info('rows: %s', len(rows))
    logging.debug('LEAVE')
    return rows

def query_findoutmore(headword):
    logging.debug('ENTER %s: ', headword)
    cursor = DB.execute('''SELECT HEADWORD, TYPE FROM HEADWORDS, FINDOUTMORE
        WHERE HEADWORDS.ROWID = FINDOUTMORE.REF AND FINDOUTMORE.HW = ?;''', [headword])
    rows = cursor.fetchall()
    logging.info('rows: %s', len(rows))
    logging.debug('LEAVE')
    return rows
    
    
HEADWORS_TXTFILE_LINE_PATTERN = re.compile(r'\A([\w\s&]+)\n+\Z')
FINDOUTMORE_TXTFILE_LINE_PATTERN = re.compile(r'\A(\d+) -> (\d+) : (\d+)\n+\Z')

HEADWORDS = list()
FINDOUTMORE = list()

def process_headwords_txtfile_line(line):
    """Get a headword from a line of string from headword.txt."""
    m = HEADWORS_TXTFILE_LINE_PATTERN.match(line)
    if m:
        HEADWORDS.append(m.group(1))
        insert_headword(m.groups())

def process_findoutmore_txtfile_line(line):
    """Get a headword from a line of string from findoutmore.txt."""
    m = FINDOUTMORE_TXTFILE_LINE_PATTERN.match(line)
    if m:
        FINDOUTMORE.append(m.groups())
        insert_findoutmore(m.groups())
        

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
        #open_db()
        #process_headwords_txtfile('headwords.txt')
        #process_findoutmore_txtfile('findoutmore.txt')
        #for i, headword in enumerate(HEADWORDS):
        #    self.lstHeadwords.insert(i, headword)
        rows = query_headwords()
        for row in rows:
            self.lstHeadwords.insert(row[0], row[1])
        logging.debug('LEAVE')

    def handler_listbox_selected(self, event):
        logging.debug('ENTER')
        curselection = self.lstHeadwords.curselection()
        logging.info('curselection: %s', curselection)
        if curselection == ():
            return
        self.lstFindoutmore.delete(0, tk.END)
        #for i, [fr, to, tp] in enumerate(FINDOUTMORE):
        #    if int(fr) == curselection[0]:
        #        self.lstFindoutmore.insert(tk.END, HEADWORDS[int(to)])
        rows = query_findoutmore(curselection[0])
        for row in rows:
            self.lstFindoutmore.insert(tk.END, row[0])
        logging.debug('LEAVE')
        
app = Application()
app.mainloop()

DB.commit()
DB.close()
logging.info('End logging ...')
