"""yoes is short for "Young Oxford Encyclopedia of Science", which is a name of a book.
The book is organized into many HEADWORDS, which are referenced much by each other.
This script is to analyze the dependance relationship between the HEADWORDS and to find
a proper learning sequence.
"""

import re
import fileinput
import tkinter as tk
import tkinter.ttk as ttk
import logging
import sqlite3

LOGGING_FORMAT =        '[%(levelname)5s] %(asctime)s %(msecs)3d <%(process)d:%(thread)d:%(threadName)10s> ' + \
                        '{%(filename)s:%(lineno)4d%(funcName)30s} %(message)s'
LOGGING_DATE_FORMAT =   '%Y-%m-%d %H:%M:%S'

logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATE_FORMAT,
    filename='yoes.log',
    filemode='w')

logging.info('Start logging ...')

class YoesStorage:
    def __init__(self):
        self.DB_FILENAME =          'yoes.db'
        self.HEADWORDS_FILENAME =   'headwords.txt'
        self.FINDOUTMORE_FILENAME = 'findoutmore.txt'

    def open(self):
        pass
    def close(self):
        pass

class DbStorage():
    def db_open(self, dbname):
        logging.debug('ENTER: %s', dbname)
        self.__db = sqlite3.connect(dbname)
        logging.info('db opened: %s', dbname)
        logging.debug('LEAVE')
    
    def db_close(self):
        logging.debug('ENTER')
        self.__db.commit()
        self.__db.close()
        logging.info('db closed')
        logging.debug('LEAVE')

    def create_tables(self):
        logging.debug('ENTER')
        self.__db.execute('''CREATE TABLE IF NOT EXISTS HEADWORDS(
            HEADWORD    TEXT    NOT NULL UNIQUE
            );''')
        logging.info('CREATE TABLE HEADWORDS')
        self.__db.execute('''CREATE TABLE IF NOT EXISTS FINDOUTMORE(
            FROM_ID     INT     NOT NULL,
            TO_ID       INT     NOT NULL,
            TYPE_ID     INT     DEFAULT(0),
            PRIMARY KEY(FROM_ID, TO_ID)
            );''')
        logging.info('CREATE TABLE FINDOUTMORE')
        logging.debug('LEAVE')

    def insert_headword(self, headword):
        logging.debug('ENTER: %s', headword)
        self.__db.execute('''INSERT OR REPLACE INTO HEADWORDS VALUES(?);''', [headword])
        logging.info('headword added: %s', headword)
        logging.debug('LEAVE')

    def insert_findoutmore(self, findoutmore):
        logging.debug('ENTER: %s', findoutmore)
        self.__db.execute('''INSERT OR REPLACE INTO FINDOUTMORE VALUES(?, ?, ?);''', findoutmore)
        logging.info('findoutmore added: %s', findoutmore)
        logging.debug('LEAVE')

    def query_headwords(self, key):
        logging.debug('ENTER')
        logging.info('key: %s', key)
        if key == None or key == '':
            cursor = self.__db.execute('''SELECT ROWID, HEADWORD FROM HEADWORDS;''')
        else:
            cursor = self.__db.execute('''SELECT ROWID, HEADWORD FROM HEADWORDS WHERE HEADWORD LIKE ?;''', ['%'+key+'%'])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_findoutmore(self, headword):
        logging.debug('ENTER: %s', headword)
        cursor = self.__db.execute('''SELECT H2.HEADWORD FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
            WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID 
            AND H1.HEADWORD = ?;''', [headword])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_findoutmore_type(self, headword, findoutmore):
        logging.debug('ENTER: %s -> %s', headword, findoutmore)
        cursor = self.__db.execute('''SELECT FINDOUTMORE.TYPE_ID FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
            WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID
            AND H1.HEADWORD = ? AND H2.HEADWORD = ?;''', [headword, findoutmore])
        row = cursor.fetchone()
        logging.info('row: %s', row)
        logging.debug('LEAVE')
        return row

class TxtfileStorage:
    def __init__(self, db):
        self.HEADWORS_TXTFILE_LINE_PATTERN = re.compile(r'\A([\w\s&-]+)\n+\Z')
        self.FINDOUTMORE_TXTFILE_LINE_PATTERN = re.compile(r'\A(\d+) -> (\d+) : (\d+)\n+\Z')
        self.HEADWORDS = list()
        self.FINDOUTMORE = list()
        self.db = db

    def process_headwords_txtfile_line(self, line):
        """Get a headword from a line of string from headword.txt."""
        m = self.HEADWORS_TXTFILE_LINE_PATTERN.match(line)
        if m:
            headword = m.group(1)
            self.HEADWORDS.append(headword)
            self.db.insert_headword(headword)

    def process_findoutmore_txtfile_line(self, line):
        """Get a headword from a line of string from findoutmore.txt."""
        m = self.FINDOUTMORE_TXTFILE_LINE_PATTERN.match(line)
        if m:
            (fr_id, to_id, type_id) = m.groups()
            findourmore = (int(fr_id) + 1, int(to_id) + 1, int(type_id))
            self.FINDOUTMORE.append(findourmore)
            self.db.insert_findoutmore(findourmore)
            

    def process_headwords_txtfile(self, filename):
        """process headword.txt file line by line."""
        logging.debug('ENTER')
        logging.info('filename: %s', filename)
        with fileinput.input(files=filename) as f:
            for line in f:
                self.process_headwords_txtfile_line(line)
        logging.debug('LEAVE')

    def process_findoutmore_txtfile(self, filename):
        """process findoutmore.txt file line by line."""
        logging.debug('ENTER')
        logging.info('filename: %s', filename)
        with fileinput.input(files=filename) as f:
            for line in f:
                self.process_findoutmore_txtfile_line(line)
        logging.debug('LEAVE')

class YoesApplication(tk.Frame):
    def __init__(self, master=None):
        logging.debug('ENTER Application.__init__()')
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        self.master.title('The Young Oxford Encyclopedia of Science')
        self.bind('<Destroy>', self.on_destroy)
        self.last_query_headword_key = ''

        self.db = DbStorage()
        self.db.db_open('yoes.db')

        #self.txtfile = TxtfileStorage(self.db)
        #self.db.create_tables()
        #self.txtfile.process_headwords_txtfile('headwords.txt')
        #self.txtfile.process_findoutmore_txtfile('findoutmore.txt')

        self.create_widgets()
        self.init_widgets()
        logging.debug('LEAVE Application.__init__()')
    
    def create_widgets(self):
        logging.debug('ENTER')

        self.var_ent_headword = tk.StringVar()
        self.entHeadword = tk.Entry(self, textvariable=self.var_ent_headword)
        self.entHeadword.grid()
        self.entHeadword.bind('<KeyRelease>', self.on_entHeadword_changed)

        self.lstHeadwords = tk.Listbox(self)
        self.lstHeadwords.grid()
        self.lstHeadwords.bind('<<ListboxSelect>>', self.on_lstHeadwords_selected)

        self.var_ent_findoutmore = tk.StringVar()
        self.entFindoutmore = tk.Entry(self, textvariable=self.var_ent_findoutmore)
        self.entFindoutmore.grid()

        self.lstFindoutmore = tk.Listbox(self)
        self.lstFindoutmore.grid()
        self.lstFindoutmore.bind('<<ListboxSelect>>', self.on_lstFindourmore_selected)

        self.OPTION_LIST_TYPE = ('Undefined', 'Depends', 'Equals')
        self.var_opt_type = tk.StringVar()
        self.optType = tk.OptionMenu(self, self.var_opt_type, *self.OPTION_LIST_TYPE)
        self.optType.grid()

        logging.debug('LEAVE')

    def init_widgets(self):
        logging.debug('ENTER')
        rows = self.db.query_headwords('')
        for row in rows:
            self.lstHeadwords.insert(row[0], row[1])
        logging.debug('LEAVE')

    def on_destroy(self, event):
        logging.debug('ENTER')
        self.db.db_close()
        logging.debug('LEAVE')

    def on_entHeadword_changed(self, event):
        logging.debug('ENTER')
        key = self.var_ent_headword.get()
        if (self.last_query_headword_key == key):
            return True

        self.last_query_headword_key = key
        logging.info('key: %s', key)
        rows = self.db.query_headwords(key)
        self.lstHeadwords.delete(0, tk.END)
        for row in rows:
            self.lstHeadwords.insert(tk.END, row[1])
        self.update_idletasks()
        logging.debug('LEAVE')
        return True

    def on_lstHeadwords_selected(self, event):
        logging.debug('ENTER')
        curselection = self.lstHeadwords.curselection()
        logging.info('curselection: %s', curselection)

        if curselection == ():
            return

        curheadwordstr = self.lstHeadwords.get(curselection[0])
        logging.info('curselectionstr: %s', curheadwordstr)
        self.var_ent_headword.set(curheadwordstr)

        logging.info('query_findoutmore: %s', curheadwordstr)
        rows = self.db.query_findoutmore(curheadwordstr)

        self.lstFindoutmore.delete(0, tk.END)
        for row in rows:
            self.lstFindoutmore.insert(tk.END, row[0])
        logging.debug('LEAVE')

    def on_lstFindourmore_selected(self, event):
        logging.debug('ENTER')
        curselection = self.lstFindoutmore.curselection()
        logging.info('curselection: %s', curselection)

        if curselection == ():
            return

        curfindourmorestr = self.lstFindoutmore.get(curselection[0])
        curheadwordstr = self.var_ent_headword.get() 
        self.var_ent_findoutmore.set(curfindourmorestr)

        logging.info('query_findoutmore_type: %s - > %s', curheadwordstr, curfindourmorestr)
        row = self.db.query_findoutmore_type(curheadwordstr, curfindourmorestr)
        self.var_opt_type.set(self.OPTION_LIST_TYPE[row[0]])
        logging.debug('LEAVE')
        
app = YoesApplication()
app.mainloop()

logging.info('End logging ...')
