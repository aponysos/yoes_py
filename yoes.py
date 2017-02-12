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

class DbStorage():
    def db_open(self, dbname):
        logging.debug('ENTER: %s', dbname)
        self.__db = sqlite3.connect(dbname)
        logging.info('db opened: %s', dbname)
        logging.debug('LEAVE')

    def db_save(self):
        logging.debug('ENTER')
        self.__db.commit()
        logging.debug('db saved')
        logging.debug('LEAVE')

    def db_close(self):
        logging.debug('ENTER')
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
        self.__db.execute("""CREATE VIEW IF NOT EXISTS V_FINDOUTMORE(FROM_HEADWORD, TO_HEADWORD, TYPE_ID)
            AS SELECT H1.HEADWORD, H2.HEADWORD, FINDOUTMORE.TYPE_ID FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
            WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID;""")
        logging.info('CREATE VIEW V_FINDOUTMORE')
        logging.debug('LEAVE')

    def insert_headword(self, headword):
        logging.debug('ENTER: %s', headword)
        self.__db.execute('''INSERT OR REPLACE INTO HEADWORDS VALUES(?);''', [headword])
        logging.debug('headword added: %s', headword)
        logging.debug('LEAVE')

    def insert_findoutmore(self, findoutmore):
        logging.debug('ENTER: %s', findoutmore)
        self.__db.execute('''INSERT OR REPLACE INTO FINDOUTMORE
            SELECT FROM_ID, TO_ID, ? FROM FINDOUTMORE, HEADWORDS H1, HEADWORDS H2
            WHERE FROM_ID = H1.ROWID AND TO_ID = H2.ROWID
            AND H1.HEADWORD = ? AND H2.HEADWORD = ?;''', findoutmore)
        logging.debug('findoutmore added: %s', findoutmore)
        logging.debug('LEAVE')

    def query_headwords_bykey(self, key=None):
        logging.info('ENTER: %s', key)
        if key == None or key == '':
            cursor = self.__db.execute('''SELECT HEADWORD FROM HEADWORDS 
                ORDER BY HEADWORD ASC;''')
        else:
            cursor = self.__db.execute('''SELECT HEADWORD FROM HEADWORDS WHERE HEADWORD LIKE ?  
                ORDER BY HEADWORD ASC;''', ['%'+key+'%'])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_from_headwords(self, to_headword):
        logging.info('ENTER: %s', to_headword)
        cursor = self.__db.execute('''SELECT FROM_HEADWORD FROM V_FINDOUTMORE 
            WHERE TO_HEADWORD = ? ORDER BY FROM_HEADWORD ASC;''', [to_headword])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_to_headwords(self, from_headword):
        logging.info('ENTER: %s', from_headword)
        cursor = self.__db.execute('''SELECT TO_HEADWORD FROM V_FINDOUTMORE 
            WHERE FROM_HEADWORD = ? ORDER BY TO_HEADWORD ASC;''', [from_headword])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_type(self, headword, findoutmore):
        logging.info('ENTER: %s -> %s', headword, findoutmore)
        cursor = self.__db.execute('''SELECT TYPE_ID FROM V_FINDOUTMORE
            WHERE FROM_HEADWORD = ? AND TO_HEADWORD = ?;''', [headword, findoutmore])
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
        logging.debug('filename: %s', filename)
        with fileinput.input(files=filename) as f:
            for line in f:
                self.process_headwords_txtfile_line(line)
        logging.debug('LEAVE')

    def process_findoutmore_txtfile(self, filename):
        """process findoutmore.txt file line by line."""
        logging.debug('ENTER')
        logging.debug('filename: %s', filename)
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
        self.last_query_findoutmore_key = ''

        self.db = DbStorage()
        self.db.db_open('yoes.db')

        #self.txtfile = TxtfileStorage(self.db)
        #self.db.create_tables()
        #self.txtfile.process_headwords_txtfile('headwords.txt')
        #self.txtfile.process_findoutmore_txtfile('findoutmore.txt')
        #self.db.db_save()

        self.create_widgets()
        logging.debug('LEAVE Application.__init__()')
    
    def create_widgets(self):
        logging.debug('ENTER')

        self.var_ent_headword = tk.StringVar()
        self.entHeadword = tk.Entry(self, name='entHeadword', textvariable=self.var_ent_headword)
        self.entHeadword.grid()

        self.lstHeadwords = tk.Listbox(self, name='lstHeadwords')
        self.lstHeadwords.grid()

        self.var_ent_findoutmore = tk.StringVar()
        self.entFindoutmore = tk.Entry(self, name='entFindoutmore', textvariable=self.var_ent_findoutmore)
        self.entFindoutmore.grid()

        self.lstFindoutmore = tk.Listbox(self, name='lstFindoutmore')
        self.lstFindoutmore.grid()

        self.OPTION_LIST_TYPE = dict(Undefined=0, Depends=1, RDepends=2)
        self.var_opt_type = tk.StringVar()
        self.optType = tk.OptionMenu(self, name='optType',, self.var_opt_type, *self.OPTION_LIST_TYPE.keys())
        self.optType.grid()

        self.btnCommit = tk.Button(self, text='Commit', command=self.commit_modification)
        self.btnCommit.grid()

        def on_keyrelease_entHeadwords(event):
            return self.showkey_headwords(listbox=self.lstHeadwords, keystr=self.var_ent_headword.get())
        def on_keyrelease_entFindoutmore(event):
            return self.showkey_headwords(listbox=self.lstFindoutmore, keystr=self.var_ent_findoutmore.get())
        self.entHeadword.bind('<KeyRelease>', on_keyrelease_entHeadwords)
        self.entFindoutmore.bind('<KeyRelease>', on_keyrelease_entFindoutmore)

        def on_keypress_escape_lstHeadwords(event):
            return self.showall_headwords(listbox=self.lstHeadwords, anchorstr=self.var_ent_headword.get())
        def on_keypress_escape_lstFindoutmore(event):
            return self.showall_headwords(listbox=self.lstFindoutmore, anchorstr=self.var_ent_findoutmore.get())
        self.lstHeadwords.bind('<KeyPress-Escape>', on_keypress_escape_lstHeadwords)
        self.lstFindoutmore.bind('<KeyPress-Escape>', on_keypress_escape_lstFindoutmore)

        def on_listbox_select_lstHeadwords(event):
            return self.select_headword(listbox=self.lstHeadwords, varstr=self.var_ent_headword)
        def on_listbox_select_lstFindoutmore(event):
            return self.select_headword(listbox=self.lstFindoutmore, varstr=self.var_ent_findoutmore)
        self.lstHeadwords.bind('<<ListboxSelect>>', on_listbox_select_lstHeadwords)
        self.lstFindoutmore.bind('<<ListboxSelect>>', on_listbox_select_lstFindoutmore)

        self.showall_headwords(listbox=self.lstHeadwords)

        logging.debug('LEAVE')

    def on_destroy(self, event):
        logging.debug('ENTER')
        self.db.db_close()
        logging.debug('LEAVE')

    def showall_headwords(self, listbox, anchorstr=None):
        logging.info('ENTER: %s, %s', anchorstr, listbox.winfo_name())
        rows = self.showkey_headwords(listbox, None)

        if anchorstr != None:
            index = rows.index(tuple([anchorstr]))
            listbox.see(index)
        logging.debug('LEAVE')

    def showkey_headwords(self, listbox, keystr=None):
        logging.info('ENTER: %s, %s', keystr, listbox.winfo_name())
        rows = self.db.query_headwords_bykey(keystr)

        listbox.delete(0, tk.END)
        for row in rows:
            listbox.insert(tk.END, row[0])

        return rows
        logging.debug('LEAVE')

    def select_headword(self, listbox, varstr):
        logging.info('ENTER: %s, %s', varstr.get(), listbox.winfo_name())
        cursel_headword = listbox.curselection()
        if cursel_headword == ():
            return
        curstr_headword = listbox.get(cursel_headword[0])
        varstr.set(curstr_headword)
        logging.info('curselectionstr: %s', curstr_headword)

        if listbox == self.lstHeadwords:
            rows = self.db.query_to_headwords(curstr_headword)
            reflistbox = self.lstFindoutmore
        else:
            rows = self.db.query_from_headwords(curstr_headword)
            reflistbox = self.lstHeadwords

        reflistbox.delete(0, tk.END)
        for row in rows:
            reflistbox.insert(tk.END, row[0])

        self.display_type()
        logging.debug('LEAVE')

    def display_type(self):
        logging.debug('ENTER')
        curstr_headword = self.var_ent_headword.get() 
        curstr_findoutmore = self.var_ent_findoutmore.get()

        row = self.db.query_type(curstr_headword, curstr_findoutmore)

        if row == None:
            self.var_opt_type.set('')
        else:
            self.var_opt_type.set(list(self.OPTION_LIST_TYPE.keys())[row[0]])
        logging.debug('LEAVE')

    def commit_modification(self):
        logging.debug('ENTER')
        findoutmore = [
            self.OPTION_LIST_TYPE[self.var_opt_type.get()], 
            self.var_ent_headword.get(), 
            self.var_ent_findoutmore.get()]
        logging.info('findoutmore: %s', findoutmore)
        self.db.insert_findoutmore(findoutmore)
        self.db.db_save()
        logging.debug('LEAVE')

app = YoesApplication()
app.mainloop()

logging.info('End logging ...')
