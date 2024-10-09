
from flask import Flask, request, redirect, render_template, session
import os
import pymysql
import boto3 as boto3
online_shopping_region = 'us-east-1'
bucket_name_online_shopping = "online-shopping-s3-bucket"
email_source_online_shopping = ''
_s3_client_online_shopping = boto3.client('s3', aws_access_key_id="", aws_secret_access_key="")
ses_client_online_shopping = boto3.client('ses', aws_access_key_id="", aws_secret_access_key="", region_name=online_shopping_region)
# conn = pymysql.connect(host="localhost", user="root", password="pranathi", db="online_shopping")
conn = pymysql.connect(host="online-shopping-rds.cowk9gdrbbr0.us-east-1.rds.amazonaws.com", user="admin", password="admin123", db="online_shopping")
cursor = conn.cursor()

app = Flask(__name__)
app.secret_key = "session"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static/products"

admin_username = "admin"
admin_password = "admin"


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/admin_login", methods=['post'])
def admin_login():
    username = request.form.get("username")
    password = request.form.get("password")
    session['role'] = "admin"
    if username == admin_username and password == admin_password:
        return redirect("/admin_home")
    else:
        return render_template("msg.html", message="invalid login details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/add_categories")
def add_categories():
    return render_template("add_categories.html")


@app.route("/add_category1", methods=['post'])
def add_category1():
    category_name = request.form.get("category_name")
    count = cursor.execute("select * from categories where category_name = '"+str(category_name)+"'")
    if count > 0:
        return render_template("msg.html", message="Duplicate Category Name")
    try:
        cursor.execute("insert into categories(category_name)values('"+str(category_name)+"')")
        conn.commit()
        return redirect("/view_categories")
    except Exception as e:
        print(e)
        return render_template("a_msg.html", message="category not added")


@app.route("/view_categories")
def view_categories():
    cursor.execute("select * from categories")
    categories = cursor.fetchall()
    return render_template("view_categories.html", categories=categories)


@app.route("/add_products")
def add_products():
    cursor.execute("select * from categories")
    categories = cursor.fetchall()
    return render_template("add_products.html", categories=categories)


@app.route("/add_product1", methods=['post'])
def add_product1():
    category_id = request.form.get("category_id")
    product_name = request.form.get("product_name")
    image = request.files.get("image")
    price = request.form.get("price")
    quantity = request.form.get("quantity")
    description = request.form.get("description")
    try:
        path = APP_ROOT+"/"+image.filename
        image.save(path)
        _s3_client_online_shopping.upload_file(path, bucket_name_online_shopping, image.filename)
        image_name = image.filename
        image_link = f'https://{bucket_name_online_shopping}.s3.amazonaws.com/{image_name}'
        cursor.execute("insert into products(category_id,product_name,image,price,quantity,description)values('"+str(category_id)+"','"+str(product_name)+"','"+str(image_link)+"','"+str(price)+"','"+str(quantity)+"','"+str(description)+"')")
        conn.commit()
        return render_template("a_msg.html", message="Product Added Successfully")
    except Exception as e:
        print(e)
        return render_template("a_msg.html", message="Product Not Added")


@app.route("/view_products")
def view_products():
    cursor.execute("select * from products")
    products = cursor.fetchall()
    return render_template("view_products.html", products=products, get_categories_by_category_id=get_categories_by_category_id)


@app.route("/view_products_customer")
def view_products_customer():
    cursor.execute("select * from categories")
    categories = cursor.fetchall()
    return render_template("view_products_customer.html", categories=categories)


@app.route("/get_products")
def get_products():
    category_id = request.args.get("category_id")
    product_name = request.args.get("product_name")
    query = ""
    if category_id != "":
        query = "select * from products where category_id='"+str(category_id)+"' and product_name like'%"+product_name+"%'"
    else:
        query = "select * from products where product_name like'%"+product_name+"%'"
    cursor.execute(query)
    products = cursor.fetchall()
    return render_template("get_products.html", products=products, get_categories_by_category_id=get_categories_by_category_id)


def get_categories_by_category_id(category_id):
    cursor.execute("select * from categories where category_id='"+str(category_id)+"'")
    categories = cursor.fetchall()
    return categories[0]


@app.route("/customer_registration")
def customer_registration():
    return render_template("customer_registration.html")


@app.route("/customer_register_action", methods=["post"])
def customer_register_action():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    location = request.form.get("location")
    address = request.form.get("address")
    count = cursor.execute("select * from customers where email = '"+str(email)+"' or phone = '" + str(phone) + "'")
    if count == 0:
        customer_emails = ses_client_online_shopping.list_identities(
            IdentityType='EmailAddress'
        )
        if email in customer_emails['Identities']:
            customer_info = 'Hi' + '' + name + ' You Have Registered Sucessfully into the Website as an User'
            ses_client_online_shopping.send_email(Source=email_source_online_shopping, Destination={'ToAddresses': [email]},
                                            Message={'Subject': {'Data': customer_info, 'Charset': 'utf-8'},
                                                     'Body': {'Html': {'Data': customer_info, 'Charset': 'utf-8'}}})
            cursor.execute("insert into customers(name,email,password,phone,gender,location,address)values('"+str(name)+"','"+str(email)+"','"+str(password)+"','"+str(phone)+"','"+str(gender)+"','"+str(location)+"','"+str(address)+"')")
            conn.commit()
            return render_template("msg.html", message="register successfully")
        else:
            return render_template("msg.html", message="Your email is not verified by website.")
    else:
        return render_template("msg.html", message="Duplicate Details")

@app.route("/customer_email_verification")
def customer_email_verification():
    return render_template("customer_email_verification.html")

@app.route("/customer_email_verification1")
def customer_email_verification1():
    email = request.args.get("email")
    ses_client_online_shopping.verify_email_address(
        EmailAddress=email
    )
    return render_template("msg.html", message="Click on the link that sent to your emailaddress")

@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")


@app.route("/customer_login_action", methods=['post'])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from customers where email='" + str(email) + "' and password='" + str(password) + "' ")
    if count > 0:
        customer = cursor.fetchall()
        emails = ses_client_online_shopping.list_identities(
            IdentityType='EmailAddress'
        )
        if email in emails['Identities']:
            info_customer = 'You' + '' + ' have Sucessfully Logged In to Website as Customer'
            ses_client_online_shopping.send_email(Source=email_source_online_shopping, Destination={'ToAddresses': [email]},
                                            Message={'Subject': {'Data': info_customer, 'Charset': 'utf-8'},
                                                     'Body': {'Html': {'Data': info_customer, 'Charset': 'utf-8'}}})
            session['customer_id'] = customer[0][0]
            session['role'] = 'customer'
            return redirect("/customer_home")
        else:
            return render_template("msg.html", message="Customer Your Email wasn't Verified", color="bg-danger text-white")
    else:
        return render_template("msg.html", message="invalid login details")


@app.route("/customer_home")
def customer_home():
    customer_id = session['customer_id']
    cursor.execute("select * from customers where customer_id ='" + str(customer_id) + "'")
    customers = cursor.fetchall()
    return render_template("customer_home.html", customer=customers[0])


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/add_cart")
def add_cart():
    product_id = request.args.get("product_id")
    quantity = request.args.get("quantity")
    customer_id = session['customer_id']
    count = cursor.execute("select * from customer_orders where customer_id='"+str(customer_id)+"' and status='cart'")
    if count > 0:
        customer_orders = cursor.fetchall()
        customer_order_id = customer_orders[0][0]
    else:
        cursor.execute("insert into customer_orders(customer_id,status)values('"+str(customer_id)+"','cart')")
        conn.commit()
        customer_order_id = cursor.lastrowid
    count = cursor.execute("select * from customer_order_items where product_id='"+str(product_id)+"' and customer_order_id='"+str(customer_order_id)+"'")
    if count > 0:
        cursor.execute("update customer_order_items set quantity=quantity+'"+str(quantity)+"' where product_id='"+str(product_id)+"'")
        conn.commit()
        return render_template("c_msg.html", message="product updated")
    else:
        cursor.execute("insert into customer_order_items(product_id,customer_order_id,quantity)values('"+str(product_id)+"','"+str(customer_order_id)+"','"+str(quantity)+"')")
        conn.commit()
        return render_template("c_msg.html", message="product added to cart")


@app.route("/view_cart")
def view_cart():
    role = session['role']
    type = request.args.get("type")
    print(role)
    print(type)
    query = " "
    if role == 'admin':
        if type == 'ordered':
            query = "select * from customer_orders where (status='ordered')"
        elif type == 'processing':
            query = "select * from customer_orders where (status='dispatched')"
        elif type == 'history':
            query = "select * from customer_orders where (status='cancelled' or status='delivered')"
    elif role == 'customer':
        customer_id = session['customer_id']
        if type == 'cart':
            query = "select * from customer_orders where customer_id='"+str(customer_id)+"' and (status='cart')"
        elif type == 'processing':
            query = "select * from customer_orders where customer_id='"+str(customer_id)+"' and (status='ordered' or status='dispatched')"
        elif type == 'history':
            query = "select * from customer_orders where customer_id='"+str(customer_id)+"' and (status='cancelled' or status='delivered' or status='Out Of Stock')"
    cursor.execute(query)
    customer_orders = cursor.fetchall()
    return render_template("view_cart.html", customer_orders=customer_orders, get_customer_by_customer_id=get_customer_by_customer_id, get_customer_order_items_by_customer_order_id=get_customer_order_items_by_customer_order_id, get_categories_by_category_id=get_categories_by_category_id, get_product_by_product_id=get_product_by_product_id, int=int)


@app.route("/order_now")
def order_now():
    customer_order_id = request.args.get("customer_order_id")
    totalPrice = request.args.get("totalPrice")
    cursor.execute("select * from customer_order_items where customer_order_id='"+str(customer_order_id)+"'")
    return render_template("order.html", customer_order_id=customer_order_id, totalPrice=totalPrice)


@app.route("/set_status")
def set_status():
    customer_order_id = request.args.get("customer_order_id")
    status = request.args.get("status")
    cursor.execute("update customer_orders set status='"+str(status)+"' where customer_order_id='"+str(customer_order_id)+"'")
    conn.commit()
    if session['role'] == 'admin':
        return render_template("a_msg.html", message="status updated successfully")
    else:
        return render_template("c_msg.html", message="status updated successfully")


@app.route("/pay_amount")
def pay_amount():
    customer_order_id = request.args.get("customer_order_id")
    cursor.execute("update customer_orders set status='ordered' where customer_order_id = '" + str(customer_order_id) + "'")
    conn.commit()
    cursor.execute("select * from customer_order_items where customer_order_id = '" + str(customer_order_id) + "'")
    customer_order_items = cursor.fetchall()
    for customer_order_item in customer_order_items:
        quantity = customer_order_item[3]
        product_id = customer_order_item[1]
        count = cursor.execute("select * from products where product_id='"+str(product_id)+"' and quantity>='" + quantity + "'")
        if count > 0:
            cursor.execute("update products set quantity=quantity-'"+str(customer_order_item[3]) + "' where product_id='" + str(customer_order_item[1]) + "'")
            conn.commit()
        else:
            cursor.execute("update customer_order_items set status='Not Available' where customer_order_item_id='" + str(customer_order_item[0]) + "'")
            conn.commit()
            count = cursor.execute("select * from customer_order_items where customer_order_id = '" + str(customer_order_id) + "' and status='available'")
            if count == 0:
                cursor.execute("update customer_orders set status='Out Of Stock' where customer_order_id = '" + str(customer_order_id) + "'")
                conn.commit()
                return render_template("cmsg.html", message="Payment has returned product is in out of stock")

    return render_template("c_msg.html", message="ordered successfully")


@app.route("/remove_from_cart")
def remove_from_cart():
    customer_order_item_id = request.args.get("customer_order_item_id")
    cursor.execute("select * from customer_order_items where customer_order_item_id='"+str(customer_order_item_id)+"'")
    customer_order_items = cursor.fetchall()
    customer_order_id = customer_order_items[0][2]
    cursor.execute("delete from customer_order_items where customer_order_item_id='"+str(customer_order_item_id)+"'")
    conn.commit()
    count = cursor.execute("select * from customer_order_items where customer_order_id='"+str(customer_order_id)+"'")
    if count == 0:
        cursor.execute("delete from customer_orders where customer_order_id='"+str(customer_order_id)+"'")
        conn.commit()
        return render_template("c_msg.html", message="removed successfully")
    else:
        return redirect("/view_cart?type=cart")


def get_customer_by_customer_id(customer_id):
    cursor.execute("select * from customers where customer_id='"+str(customer_id)+"'")
    customers = cursor.fetchall()
    return customers[0]


def get_customer_order_items_by_customer_order_id(customer_order_id):
    cursor.execute("select * from customer_order_items where customer_order_id='"+str(customer_order_id)+"'")
    customer_order_items = cursor.fetchall()
    return customer_order_items


def get_product_by_product_id(product_id):
    cursor.execute("select * from products where product_id = '"+str(product_id)+"'")
    products = cursor.fetchall()
    return products[0]


app.run(debug=True)
