from db.connection import get_connection

def get_user(user_id):
    conn=get_connection()
    cur = conn.cursor()
    cur.execute("Select*from users where id %s",user_id)

    user=cur.fetchone()
    conn.close()
    return user