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
            HEADWORD    TEXT        NOT NULL UNIQUE
            LEVEL       INTERGER    NOT NULL DEFAULT(-1)
            );''')
        logging.info('CREATE TABLE HEADWORDS')
        self.__db.execute('''CREATE TABLE IF NOT EXISTS FINDOUTMORE(
            FROM_ID     INT         NOT NULL,
            TO_ID       INT         NOT NULL,
            TYPE_ID     INT         DEFAULT(0),
            PRIMARY KEY(FROM_ID, TO_ID)
            );''')
        logging.info('CREATE TABLE FINDOUTMORE')
        self.__db.execute("""CREATE VIEW IF NOT EXISTS V_FINDOUTMORE(FROM_HEADWORD, TO_HEADWORD, TYPE_ID)
            AS SELECT H1.HEADWORD, H2.HEADWORD, FINDOUTMORE.TYPE_ID FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
            WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID;""")
        logging.info('CREATE VIEW V_FINDOUTMORE')
        logging.debug('LEAVE')

    def query_headwords_bykey(self, key=None):
        logging.info('ENTER: %s', key)
        if key == None or key == '':
            cursor = self.__db.execute('''SELECT * FROM HEADWORDS 
                ORDER BY HEADWORD ASC;''')
        else:
            cursor = self.__db.execute('''SELECT * FROM HEADWORDS WHERE HEADWORD LIKE ?  
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
            WHERE FROM_HEADWORD = ? ORDER BY FROM_HEADWORD ASC;''', [from_headword])
        rows = cursor.fetchall()
        logging.info('rows: %s', len(rows))
        logging.debug('LEAVE')
        return rows

    def query_level(self, headword):
        logging.info('ENTER: %s', headword)
        cursor = self.__db.execute('''SELECT LEVEL FROM HEADWORDS WHERE HEADWORD = ?;''', [headword])
        row = cursor.fetchone()
        logging.info('row: %s', row)
        logging.debug('LEAVE')
        return row

    def query_type(self, from_headword, to_headword):
        logging.info('ENTER: %s -> %s', from_headword, to_headword)
        cursor = self.__db.execute('''SELECT TYPE_ID FROM V_FINDOUTMORE
            WHERE FROM_HEADWORD = ? AND TO_HEADWORD = ?;''', [from_headword, to_headword])
        row = cursor.fetchone()
        logging.info('row: %s', row)
        logging.debug('LEAVE')
        return row

    def insert_headword(self, headword, level=-1):
        logging.debug('ENTER: %s %s', headword, level)
        self.__db.execute('''INSERT OR REPLACE INTO HEADWORDS VALUES(?, ?);''', [headword, level])
        logging.info('headword added: %s, %s', headword, level)
        logging.debug('LEAVE')

    def update_level(self, headword, level):
        logging.debug('ENTER: %s %s', headword, level)
        self.__db.execute('''UPDATE OR ROLLBACK HEADWORDS SET LEVEL = ? WHERE HEADWORD = ?;''', [level, headword])
        logging.info('headword updated: %s, %s', headword, level)
        logging.debug('LEAVE')

    def insert_findoutmore(self, from_name, to_name, type_id):
        logging.debug('ENTER: %s -> %s : %s', from_name, to_name, type_id)
        self.__db.execute('''INSERT OR REPLACE INTO FINDOUTMORE
            SELECT FROM_ID, TO_ID, ? FROM FINDOUTMORE, HEADWORDS H1, HEADWORDS H2
            WHERE FROM_ID = H1.ROWID AND TO_ID = H2.ROWID
            AND H1.HEADWORD = ? AND H2.HEADWORD = ?;''', [type_id, from_name, to_name])
        logging.info('findoutmore added: %s -> %s : %s', from_name, to_name, type_id)
        logging.debug('LEAVE')

    def remove_findoutmore(self, from_name, to_name):
        logging.debug('ENTER: %s -> %s', from_name, to_name)
        self.__db.execute('''DELETE FROM FINDOUTMORE WHERE 
            FROM_ID IN (SELECT ROWID FROM HEADWORDS WHERE HEADWORD = ?) AND 
            TO_ID IN (SELECT ROWID FROM HEADWORDS WHERE HEADWORD = ?);''', [from_name, to_name])
        logging.info('findoutmore removed: %s -> %s', from_name, to_name)
        logging.debug('LEAVE')

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
        logging.info('ENTER')

        self.var_ent_headword = tk.StringVar()
        self.entHeadword = tk.Entry(self, name='entHeadword', textvariable=self.var_ent_headword)
        self.entHeadword.grid(row=0, column=1)

        self.lstHeadwords = tk.Listbox(self, name='lstHeadwords')
        self.lstHeadwords.grid(row=1, column=1)

        self.var_ent_findoutmore = tk.StringVar()
        self.entFindoutmore = tk.Entry(self, name='entFindoutmore', textvariable=self.var_ent_findoutmore)
        self.entFindoutmore.grid(row=0, column=2)

        self.lstFindoutmore = tk.Listbox(self, name='lstFindoutmore')
        self.lstFindoutmore.grid(row=1, column=2)

        self.var_ent_rfindoutmore = tk.StringVar()
        self.entRFindoutmore = tk.Entry(self, name='entRFindoutmore', textvariable=self.var_ent_rfindoutmore)
        self.entRFindoutmore.grid(row=0, column=0)

        self.lstRFindoutmore = tk.Listbox(self, name='lstRFindoutmore')
        self.lstRFindoutmore.grid(row=1, column=0)

        self.OPTION_TYPE_LIST = dict(Undefined=0, Depends=1, SubClass=2, RDepends=-1)
        self.var_opt_type = tk.StringVar()
        self.optType = tk.OptionMenu(self, self.var_opt_type, *self.OPTION_TYPE_LIST.keys())
        self.optType.grid(row=2, column=2)

        self.var_opt_rtype = tk.StringVar()
        self.optRType = tk.OptionMenu(self, self.var_opt_rtype, *self.OPTION_TYPE_LIST.keys())
        self.optRType.grid(row=2, column=0)

        def on_buttoncommand_btnCommit():
            self.commit_findoutmore_modification(self.var_ent_headword, self.var_ent_findoutmore, self.var_opt_type)
        self.btnCommit = tk.Button(self, text='Commit', command=on_buttoncommand_btnCommit)
        self.btnCommit.grid(row=3, column=2)

        def on_buttoncommand_btnRCommit():
            self.commit_findoutmore_modification(self.var_ent_rfindoutmore, self.var_ent_headword, self.var_opt_rtype)
        self.btnRCommit = tk.Button(self, text='Commit', command=on_buttoncommand_btnRCommit)
        self.btnRCommit.grid(row=3, column=0)

        def on_keyrelease_entHeadwords(event):
            self.listbox_showkey_headwords(listbox=self.lstHeadwords, keystr=self.var_ent_headword.get())
        def on_keyrelease_entFindoutmore(event):
            self.listbox_showkey_headwords(listbox=self.lstFindoutmore, keystr=self.var_ent_findoutmore.get())
        def on_keyrelease_entRFindoutmore(event):
            self.listbox_showkey_headwords(listbox=self.lstRFindoutmore, keystr=self.var_ent_rfindoutmore.get())
        self.entHeadword.bind('<KeyRelease>', on_keyrelease_entHeadwords)
        self.entFindoutmore.bind('<KeyRelease>', on_keyrelease_entFindoutmore)
        self.entRFindoutmore.bind('<KeyRelease>', on_keyrelease_entRFindoutmore)

        def on_keypress_escape_lstHeadwords(event):
            self.listbox_showall_headwords(listbox=self.lstHeadwords, anchorstr=self.var_ent_headword.get())
        def on_keypress_escape_lstFindoutmore(event):
            self.listbox_showall_headwords(listbox=self.lstFindoutmore, anchorstr=self.var_ent_findoutmore.get())
        def on_keypress_escape_lstRFindoutmore(event):
            self.listbox_showall_headwords(listbox=self.lstRFindoutmore, anchorstr=self.var_ent_rfindoutmore.get())
        self.lstHeadwords.bind('<KeyPress-Escape>'  , on_keypress_escape_lstHeadwords)
        self.lstFindoutmore.bind('<KeyPress-Escape>', on_keypress_escape_lstFindoutmore)
        self.lstRFindoutmore.bind('<KeyPress-Escape>', on_keypress_escape_lstRFindoutmore)

        def on_listbox_select_lstHeadwords(event):
            self.listbox_select_item(listbox=self.lstHeadwords, varstr=self.var_ent_headword)
        def on_listbox_select_lstFindoutmore(event):
            self.listbox_select_item(listbox=self.lstFindoutmore, varstr=self.var_ent_findoutmore)
        def on_listbox_select_lstRFindoutmore(event):
            self.listbox_select_item(listbox=self.lstRFindoutmore, varstr=self.var_ent_rfindoutmore)
        self.lstHeadwords.bind('<<ListboxSelect>>', on_listbox_select_lstHeadwords)
        self.lstFindoutmore.bind('<<ListboxSelect>>', on_listbox_select_lstFindoutmore)
        self.lstRFindoutmore.bind('<<ListboxSelect>>', on_listbox_select_lstRFindoutmore)

        self.trvHierarchy = ttk.Treeview(self)
        self.trvHierarchy.grid(row=0, column=3, rowspan=4, columnspan=4)

        self.OPTION_LEVEL_LIST = dict(Root=0, First=1, Second=2, Undefined=-1)
        self.var_opt_level = tk.StringVar()
        self.optLevel = tk.OptionMenu(self, self.var_opt_level, *self.OPTION_LEVEL_LIST.keys())
        self.optLevel.grid(row=2, column=1)

        def on_buttoncommand_btnUpdate():
            self.update_headword_level()
        self.btnUpdate = tk.Button(self, text='Update', command=on_buttoncommand_btnUpdate)
        self.btnUpdate.grid(row=3, column=1)

        self.listbox_showall_headwords(listbox=self.lstHeadwords)
        self.display_hierarchy()

        logging.info('LEAVE')

    def on_destroy(self, event):
        logging.debug('ENTER')
        self.db.db_close()
        logging.debug('LEAVE')

    def listbox_showall_headwords(self, listbox, anchorstr=None):
        logging.info('ENTER: %s, %s', anchorstr, listbox.winfo_name())
        rows = self.listbox_showkey_headwords(listbox, None)

        if anchorstr != None:
            index = rows.index(tuple([anchorstr]))
            listbox.see(index)
        logging.debug('LEAVE')

    def listbox_showkey_headwords(self, listbox, keystr=None):
        logging.info('ENTER: %s, %s', keystr, listbox.winfo_name())
        rows = self.db.query_headwords_bykey(keystr)

        listbox.delete(0, tk.END)
        for row in rows:
            listbox.insert(tk.END, row[0])

        return rows
        logging.debug('LEAVE')

    def listbox_select_item(self, listbox, varstr):
        logging.info('ENTER: %s, %s', varstr.get(), listbox.winfo_name())
        cursel_headword = listbox.curselection()
        if cursel_headword == ():
            return
        curstr_headword = listbox.get(cursel_headword[0])
        varstr.set(curstr_headword)
        logging.info('curselectionstr: %s', curstr_headword)

        if listbox == self.lstHeadwords:
            rows = self.db.query_to_headwords(curstr_headword)
            self.lstFindoutmore.delete(0, tk.END)
            for row in rows:
                self.lstFindoutmore.insert(tk.END, row[0])

            rrows = self.db.query_from_headwords(curstr_headword)
            self.lstRFindoutmore.delete(0, tk.END)
            for rrow in rrows:
                self.lstRFindoutmore.insert(tk.END, rrow[0])

            self.display_level()

        self.display_type()
        logging.debug('LEAVE')

    def display_type(self):
        logging.debug('ENTER')
        curstr_headword = self.var_ent_headword.get() 
        curstr_findoutmore = self.var_ent_findoutmore.get()
        curstr_rfindoutmore = self.var_ent_rfindoutmore.get()

        row = self.db.query_type(curstr_headword, curstr_findoutmore)
        if row == None:
            self.var_opt_type.set('')
        else:
            self.var_opt_type.set(list(self.OPTION_TYPE_LIST.keys())[row[0]])

        rrow = self.db.query_type(curstr_rfindoutmore, curstr_headword)
        if rrow == None:
            self.var_opt_rtype.set('')
        else:
            self.var_opt_rtype.set(list(self.OPTION_TYPE_LIST.keys())[rrow[0]])
        logging.debug('LEAVE')

    def display_level(self):
        logging.debug('ENTER')
        curstr_headword = self.var_ent_headword.get() 

        row = self.db.query_level(curstr_headword)
        if row == None:
            self.var_opt_level.set('')
        else:
            self.var_opt_level.set(list(self.OPTION_LEVEL_LIST.keys())[row[0]])
        logging.debug('LEAVE')

    def commit_findoutmore_modification(self, var_from, var_to, var_type):
        logging.debug('ENTER')
        if (var_type.get() == ''):
            return
        from_name = var_from.get()
        to_name = var_to.get()
        type_id = self.OPTION_TYPE_LIST[var_type.get()]
        logging.info('%s -> %s : %s', from_name, to_name, type_id)
        if type_id != -1:
            self.db.insert_findoutmore(from_name, to_name, type_id)
        else:
            self.db.insert_findoutmore(to_name, from_name, 0) # insert new depend
            self.db.remove_findoutmore(from_name, to_name) # remove old depend
        self.db.db_save()
        logging.debug('LEAVE')

    def update_headword_level(self):
        logging.debug('ENTER')
        if (self.var_opt_level.get() == ''):
            return
        headword = self.var_ent_headword.get()
        level = self.OPTION_LEVEL_LIST[self.var_opt_level.get()]
        logging.info('%s : %s', headword, level)
        self.db.update_level(headword, level)
        self.db.db_save()

        self.display_hierarchy()
        logging.debug('LEAVE')

    def display_hierarchy(self):
        logging.debug('ENTER')
        self.trvHierarchy.delete(*self.trvHierarchy.get_children())

        rows = self.db.query_headwords_bykey()
        for row in rows:
            if row[1] == 0:
                self.trvHierarchy.insert('', 'end', iid=row[0], text=row[0])
                self.add_tree_nodes(row[0])

        logging.debug('LEAVE')

    def add_tree_nodes(self, node_name):
        rows = self.db.query_from_headwords(node_name)
        for row in rows:
            sub_node_name = row[0]
            type_row = self.db.query_type(sub_node_name, node_name)
            if type_row != None and type_row[0] == 2:
                self.trvHierarchy.insert(node_name, 'end', iid=sub_node_name, text=sub_node_name)
                self.add_tree_nodes(sub_node_name)

app = YoesApplication()
app.mainloop()

logging.info('End logging ...')
