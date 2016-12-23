import MySQLdb
import MySQLdb.cursors


def connection():
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="sql_serv_Delo_1234",
                           db="oncat")

    dc = conn.cursor(MySQLdb.cursors.DictCursor)

    c = conn.cursor()

    return dc, c, conn
