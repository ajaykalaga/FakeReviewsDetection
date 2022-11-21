# from crypt import methods
import imp
from ipaddress import ip_address
from flask import Flask, render_template, request, redirect, session
import pickle
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
import sqlite3
import json
import uuid
from werkzeug.utils import secure_filename
import os
from flask import request
from flask import jsonify

from sqlalchemy import true
import requests

with open('config.json', 'r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.secret_key = params['Secret_Key']
path = params['db']


def text_process(review):
    nopunc = [char for char in review if char not in string.punctuation]
    nopunc = "".join(nopunc)
    return [word for word in nopunc.split() if word.lower() not in stopwords.words('english')]


def predicttt(review):
    model = pickle.load(open('model.pkl', 'rb'))
    review = [f"{review}"]
    prediction = model.predict(review)
    return prediction[0]
# def ipaddr():
    
#     hostname= socket.gethostname()
#     IPaddr= socket.gethostbyname(hostname)
#     return IPaddr

@app.route("/")
def home():
    if "u_id" in session:
        con = sqlite3.connect(path)
        cursor = con.cursor()
        cursor.execute(f"select * from users where slno ={session['u_id']}")
        user = cursor.fetchone()
        cursor.execute("select * from products")
        products = cursor.fetchall()
        return render_template("home.html", products=products, user=user)
    else:
        con = sqlite3.connect(path)
        cursor = con.cursor()
        cursor.execute("select * from products")
        products = cursor.fetchall()
        return render_template("home.html", products=products)


@app.route("/login", methods=['GET', 'POST'], strict_slashes=False)
def login():
    if(request.method == "POST"):
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute(
                f"select * from users where username = '{username}'")
            user = cursor.fetchone()
            con.close()
            if len(user) > 0:
                if user[2] == password:
                    session['u_id'] = user[0]
                    return redirect('/')
                # print(IPaddr)
            return redirect('/login')
        except Exception as e:
            print(e)
            return redirect('/')
        
        # ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        # print(ip_addr)
        
    else:
        return render_template("login.html")
    


@app.route("/register", methods=['GET', 'POST'])
def register():
    if(request.method == "POST"):
        username = request.form.get("username")
        password = request.form.get("password")
        cnfmpassword = request.form.get("cnfmpassword")
        
            
        if password == cnfmpassword:
            try:
                con = sqlite3.connect(path)
                cursor = con.cursor()
                cursor.execute(
                    f"insert into users (username,password) values ('{username}','{password}')")
                con.commit()
                con.close()
                return redirect('/login')
            except Exception as e:
                print(e)
                return redirect('/')
    else:
        return render_template("register.html")


@app.route("/product/review/<product_id>")
def productReview(product_id):
    try:
        con = sqlite3.connect(path)
        cursor = con.cursor()
        cursor.execute(
            f"select * from products where product_id = {product_id}")
        product = cursor.fetchone()
        cursor.execute(
            f"select review, username from reviews inner join users ON users.slno =  reviews.user_id where product_id = {product_id} ")
        reviews = cursor.fetchall()
        con.close()
        return render_template("reviews.html", reviews=reviews, product=product)
    except Exception as e:
        print(e)
        return redirect('/')


@app.route("/review/register/<product_id>", methods=['GET', 'POST'])
def reviewRegister(product_id):
    if 'u_id' in session:
        if request.method == 'POST':
            review = request.form.get("review")
            product_id = int(product_id)
            user_id = int(session['u_id'])
            review_type = predicttt(review)
            hostname= socket.gethostname()
            ip_address= socket.gethostbyname(hostname)
         
            try:
                con = sqlite3.connect(path)
                cursor = con.cursor()
                cursor.execute(
                    f"insert into reviews (product_id,user_id,review,review_type,ip_address) values ({product_id},{user_id},'{review}','{review_type}','{ip_address}')")
                con.commit()
                con.close()
                return redirect(f'/product/review/{product_id}')
            except Exception as e:
                print(e)
                return redirect('/')
        else:
            return render_template("adminproductregister.html")
    else:
        return redirect('/login')


@app.route("/logout")
def logout():
    session.pop('u_id')
    return redirect('/')


@app.route("/admin/login", methods=['GET', 'POST'])
def adminLogin():
    if(request.method == 'POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        if(params['admin_email'] == email and params['admin_password'] == password):
            session['admin_id'] = email
            return redirect('/admin/dashboard')
        else:
            return render_template('adminlogin.html')

    else:
        return render_template('adminlogin.html')


@app.route("/admin/dashboard")
def adminDashboard():
    if 'admin_id' in session:
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute("select * from users")
            users = cursor.fetchall()
            con.close()
            return render_template("admindashboard.html", users=users)

        except Exception as e:
            print(e)
            return redirect('/admin/login')
    else:
        return redirect('/admin/login')


@app.route("/admin/user/delete/<user_id>")
def deleteUser(user_id):
    if 'admin_id' in session:
        con = sqlite3.connect(path)
        cursor = con.cursor()
        cursor.execute(f"delete from users where slno = {user_id}")
        con.commit()
        cursor.execute(f"delete from reviews where user_id = {user_id}")
        con.commit()
        con.close()
        return redirect("/admin/dashboard")


@app.route("/admin/products")
def allProducts():
    if 'admin_id' in session:
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute("select * from products")
            products = cursor.fetchall()
            # print(products)
            return render_template("allproducts.html", products=products)

        except Exception as e:
            print(e)
    else:
        return redirect('/admin/login')


@app.route("/admin/products/delete/<product_id>")
def deleteProduct(product_id):
    if 'admin_id' in session:
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute(
                f"select product_pic from products where product_id = {product_id}")
            img = cursor.fetchone()
            os.remove(f"static/images/{img[0]}")
            cursor.execute(
                f"delete from reviews where product_id = {product_id}")
            con.commit()
            cursor.execute(
                f"delete from products where product_id = {product_id}")
            con.commit()
            con.close()
            return redirect("/admin/products")
        except Exception as e:
            print(e)
    else:
        return redirect('/admin/login')


@app.route("/admin/reviews")
def allReviwes():
    if 'admin_id' in session:
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute('''select review_id,product_name,username,review,review_type,ip_address from reviews 
                INNER JOIN products ON products.product_id = reviews.product_id
                INNER JOIN users ON users.slno = reviews.user_id''')
            reviews = cursor.fetchall()
            return render_template("allreviews.html", reviews=reviews)
        except Exception as e:
            print(e)
    else:
        return redirect('/admin/login')


@app.route("/admin/reviews/delete/<review_id>")
def deleteReview(review_id):
    if 'admin_id' in session:
        try:
            con = sqlite3.connect(path)
            cursor = con.cursor()
            cursor.execute(
                f"delete from reviews where review_id = {review_id}")
            con.commit()
            con.close()
            return redirect("/admin/reviews")

        except Exception as e:
            print(e)
    else:
        return redirect('/admin/login')


@app.route("/admin/product/register", methods=['GET', 'POST'])
def productRegister():
    if 'admin_id' in session:
        if (request.method == 'POST'):
            product_name = request.form.get('product_name')
            product_price = int(request.form.get('product_price'))
            file = request.files['product_image']
            pic_name = secure_filename(file.filename)
            picture_name = str(uuid.uuid1()) + "."+f"{pic_name.split('.')[1]}"
            file.save(f"static/images/{picture_name}")
            try:
                con = sqlite3.connect(path)
                cursor = con.cursor()
                print()
                cursor.execute(
                    f"insert into products (product_name,price,product_pic) values ('{product_name}',{product_price},'{picture_name}')")
                con.commit()
                con.close()
                return redirect("/admin/products")
            except Exception as e:
                print(e)
                return redirect('/admin/dashboard')
        else:
            return render_template("adminproductregister.html")
    else:
        return redirect("/admin/login")


@app.route("/admin/logout")
def adminLogout():
    session.pop('admin_id')
    return redirect("/admin/login")


# # 186ba788-a256-48fb-9f5f-774b2b26b189
# accessKey = "186ba788-a256-48fb-9f5f-774b2b26b189"
# response=requests.post("https://apiip.net/api/check& accessKey = "+ accessKey).json
# print(response)
import socket


if __name__ == '__main__':
    app.run(debug=True)
