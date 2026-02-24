import sqlite3

DATABASE = 'website.db'


def print_all_website():
    speed = input("What speed: ")
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        sql = "SELECT UserID,Name FROM website WHERE Name > ?;"
        cursor.execute(sql,(__name__,))
        results = cursor.fetchall()
        #print them nicely

        for website in results:
            print(f"website: {website[0]} UserID :{website[1]}")


if __name__ == "__main__":
   print_all_website()
