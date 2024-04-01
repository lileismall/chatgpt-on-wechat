import sqlite3 

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


# name_id is key in this table
'''
name | name_id | create_time 
create_time 是时间戳， name 是名字
'''
def create_db(db_file):
    sql = """ 
    CREATE TABLE IF NOT EXISTS info (
        name text NOT NULL,
        create_time DATE NOT NULL
    );
    """
    
    conn = create_connection(db_file)
    if conn is not None:
        create_table(conn, sql)
    else:
        print("Error! cannot create the database connection.")
    
    return conn

def db_exec(sql):
    conn = create_db("info.db")
    cur = conn.cursor()
    
    cur.execute(sql)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
        
    return rows

def insert_info(name):
    conn = create_db("info.db")
    sql = "INSERT INTO info(name, create_time) VALUES(?,datetime('now', '+8 hours')) "
    
    cur = conn.cursor()
    cur.execute(sql, (name,))
    conn.commit()
    
    cur.close()
    conn.close()
    return cur.lastrowid

def get_cnt_by_name(name, type):
    if type == "week":
        sql = f"""
            SELECT COUNT( * ) AS count
            FROM info
            WHERE name = '{name}' AND 
            strftime('%Y-%W', create_time) = strftime('%Y-%W', 'now', '+8 hours');
        """
    elif type == "month":
        sql = f"""
            SELECT COUNT( * ) AS count
            FROM info
            WHERE name = '{name}' AND 
            strftime('%Y-%m', create_time) = strftime('%Y-%m', 'now', '+8 hours');
        """
    elif type == "all":
        sql = f"""
            SELECT COUNT( * ) AS count
            FROM info
            WHERE name = '{name}' 
        """

    rows = db_exec(sql)
        
    return rows[0][0]

def get_week_top10():
    sql = f"""
        SELECT name, COUNT( * ) AS count
        FROM info
        WHERE strftime('%Y-%W', create_time) = strftime('%Y-%W', 'now', '+8 hours')
        GROUP BY name
        ORDER BY count DESC
        LIMIT 10;
    """
    rows = db_exec(sql)
        
    return rows

def get_month_top10():
    sql = f"""
        SELECT name, COUNT( * ) AS count
        FROM info
        WHERE strftime('%Y-%W', create_time) = strftime('%Y-%W', 'now', '+8 hours')
        GROUP BY name
        ORDER BY count DESC
        LIMIT 10;
    """
    rows = db_exec(sql)
        
    return rows

def get_all_top10():
    sql = f"""
        SELECT name, COUNT( * ) AS count
        FROM info
        WHERE strftime('%Y', create_time) = strftime('%Y', 'now', '+8 hours')
        GROUP BY name
        ORDER BY count DESC
        LIMIT 10;
    """
    rows = db_exec(sql)
        
    return rows

info = {
    "name": "lilei",
    "name_id": 123545566,
    "create_time": 123123123124
}

# if __name__ == '__main__':
#     create_db("info2.db")
#     conn = create_connection("info2.db")
#     insert_info(conn, info)
#     conn.close()