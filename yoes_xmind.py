import xmind
from xmind.core import workbook,saver
from xmind.core.topic import TopicElement
import sqlite3
import os

def query_headwords():
    cursor = db.execute('''SELECT * FROM HEADWORDS ORDER BY HEADWORD ASC;''')
    rows = cursor.fetchall()
    return rows

def query_findoutmore():
    cursor = db.execute('''SELECT * FROM V_FINDOUTMORE;''')
    rows = cursor.fetchall()
    return rows

db = sqlite3.connect("yoes.db")
db.execute("""CREATE VIEW IF NOT EXISTS V_FINDOUTMORE
    AS SELECT H1.HEADWORD FROM_HEADWORD, H2.HEADWORD TO_HEADWORD, FINDOUTMORE.TYPE_ID FROM HEADWORDS H1, FINDOUTMORE, HEADWORDS H2
    WHERE H1.ROWID = FINDOUTMORE.FROM_ID AND H2.ROWID = FINDOUTMORE.TO_ID;""")

headwords_rows = query_headwords()
findoutmore_rows = query_findoutmore()
db.close()

####################################################################################
xmind_filename = '.\\yoes.xmind'

if os.path.exists(xmind_filename):
    os.remove(xmind_filename)
workbook = xmind.load(xmind_filename) # load an existing file or create a new workbook if nothing is found

sheet = workbook.getPrimarySheet() # get the first sheet
sheet.setTitle("YOES") # set its title

root_topic = sheet.getRootTopic() # get the root topic of this sheet
root_topic.setTitle("YOES") # set its title

undefined_topic = TopicElement()
undefined_topic.setTitle("Undefined")
root_topic.addSubTopic(undefined_topic)

headwors = list()
topics = list()

for row in headwords_rows:
    headword = row[0]
    level = row[1]
    headwors.append(headword)

    topic = TopicElement(None, workbook)
    topic.setTitle(headword)
    topics.append(topic)

    if level == 0:
        root_topic.addSubTopic(topic)
    else:
        undefined_topic.addSubTopic(topic)

for row in findoutmore_rows:
    from_headword = row[0]
    to_headword = row[1]
    type_id = row[2]
    from_i = headwors.index(from_headword)
    to_i = headwors.index(to_headword)
    from_topic = topics[from_i]
    to_topic = topics[to_i]

    if type_id == 2:
        to_topic.addSubTopic(from_topic)
    elif type_id == 1:
        pass
        #rel = sheet.createRelationship(from_topic.getID(), to_topic.getID())
        #sheet.addRelationship(rel)
    elif type_id == 0:
        pass

xmind.save(workbook)
