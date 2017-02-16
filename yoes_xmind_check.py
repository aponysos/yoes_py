import xmind
from xmind.core import workbook,saver
from xmind.core.topic import TopicElement
import sqlite3
import os
import logging
from collections import deque
####################################################################################

LOGGING_FORMAT =        '[%(levelname)5s] %(asctime)s %(msecs)3d <%(process)d:%(thread)d:%(threadName)10s> ' + \
                        '{%(filename)s:%(lineno)4d%(funcName)10s} %(message)s'
LOGGING_DATE_FORMAT =   '%Y-%m-%d %H:%M:%S'

logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATE_FORMAT,
    filename='yoes_check.log',
    filemode='w')

logging.info('Start logging ...')

def query_headwords():
    cursor = db.execute('''SELECT * FROM HEADWORDS ORDER BY HEADWORD ASC;''')
    rows = cursor.fetchall()
    return rows

def query_findoutmore():
    cursor = db.execute('''SELECT * FROM V_FINDOUTMORE;''')
    rows = cursor.fetchall()
    return rows

db = sqlite3.connect("yoes.db")
logging.info('db opend: %s', db)
db.execute("""CREATE VIEW IF NOT EXISTS V_FINDOUTMORE
    AS SELECT H1.HEADWORD FROM_HEADWORD, H2.HEADWORD TO_HEADWORD, FINDOUTMORE.TYPE_ID FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
    WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID;""")

headwords_rows = query_headwords()
logging.info('query_headwords: %s', len(headwords_rows))

findoutmore_rows = query_findoutmore()
logging.info('query_findoutmore: %s', len(findoutmore_rows))

db.close()
logging.info('db closed')

####################################################################################
xmind_filename = '.\\yoes.xmind'
workbook = xmind.load(xmind_filename) # load an existing file or create a new workbook if nothing is found
logging.info('workbook loaded: %s', workbook)

sheet = workbook.getPrimarySheet() # get the first sheet
logging.info('getPrimarySheet: %s', sheet.getTitle())

root_topic = sheet.getRootTopic() # get the root topic of this sheet
logging.info('getRootTopic: %s', root_topic.getTitle())

topics = deque()
topics.append(root_topic)
headwords = list()

while len(topics) > 0:
    topic = topics.pop()
    headwords.append(topic.getTitle())
    sub_topics = topic.getSubTopics()
    if sub_topics == None:
        continue
    sub_topics.reverse()
    for t in sub_topics:
        topics.append(t)
logging.info('headwords list: %s', headwords)

for row in findoutmore_rows:
    from_headword = row[0]
    to_headword = row[1]
    type_id = row[2]

    if type_id > 0: #Depends
        from_i = headwords.index(from_headword)
        to_i = headwords.index(to_headword)
        if (from_i <= to_i): #wrong
            logging.warn('Wrong Squence: %s(%s) -> %s(%s): %s', 
            from_headword, from_i, to_headword, to_i, type_id)

logging.info('End logging ...')
