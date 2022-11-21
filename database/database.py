import sqlite3
db = sqlite3.connect("./database/ecommerce.db")
cursor = db.cursor()
cursor.execute("CREATE table users(slno INTEGER PRIMARY KEY AUTOINCREMENT,username varchar not null unique,password varchar);")
cursor.execute(
    "CREATE table products(product_id INTEGER PRIMARY KEY AUTOINCREMENT,product_name varchar,price int,product_pic varchar);")
cursor.execute("CREATE table reviews(review_id INTEGER PRIMARY KEY AUTOINCREMENT,product_id int,user_id int,review text,review_type varchar, ip_address varchar);")
db.commit()
db.close()
