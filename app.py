from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_mysqldb import MySQL  
from werkzeug.security import generate_password_hash, check_password_hash
import re
import secrets




app = Flask(__name__)

# 🔹 Secret key for session
app.secret_key = 'dcdc9c1377a438ef0d8dc4534eb6f2f8aec094a5dc65779983e8ccf15e9e898d'



# 🔹 Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'WJ28@krhps'
app.config['MYSQL_DB'] = 'pro_db'

mysql = MySQL(app) 

# ----------------- SIGNUP ROUTE -----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['user_name']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor()

        # 🔹 Check if user exists
        cursor.execute('SELECT * FROM users WHERE user_name = %s OR email = %s', (username, email))
        account = cursor.fetchone()

        if account:
            flash('Account already exists! Please log in.', 'warning')
            return redirect(url_for('login'))
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!', 'danger')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only letters and numbers!', 'danger')
        elif not username or not password or not email:
            flash('Please fill out the form completely!', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (user_name, password, email) VALUES (%s, %s, %s)', 
                           (username, hashed_password, email))
            mysql.connection.commit()

            # 🔐 Set session for auto-login
            session['loggedin'] = True
            session['user_name'] = username
            session['email'] = email

            flash('Signup successful! Redirecting to dashboard...', 'success')
            return redirect(url_for('dashboard'))

    return render_template('signup.html')

# ----------------- LOGIN ROUTE -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''

    
    if request.method == 'POST':
        username = request.form['user_name']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE user_name = %s', (username,))
        account = cursor.fetchone()

        if account and check_password_hash(account[2], password):  # ✅ Secure password check
            session['loggedin'] = True
            session['user_name'] = username  
            session['email'] = account[3]  # ✅ Store email from DB in session
            session['password'] = account[2]  # ✅ Store hashed password in session
            
            flash('You logged in successfully!', 'success')  
            return redirect(url_for('dashboard'))  
        else:
            msg = 'Incorrect username/password!'
    
    return render_template('login.html', msg=msg)

# ----------------- DASHBOARD ROUTE -----------------
from flask import Flask, render_template, redirect, url_for, session, flash

@app.route('/dashboard')
def dashboard():
    if session.get('loggedin'):
        username = session.get('user_name', 'User')  # fallback if user_name not in session
        return render_template('dashboard.html', user_name=username)

    else:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))


# ----------------- LOGOUT ROUTE -----------------
@app.route('/logout')
def logout():
    session.clear()  # ✅ Clear session
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))  

# ----------------- USER DETAILS ROUTE -----------------
@app.route('/user_details', methods=['GET', 'POST'])
def user_details():
    user_name = session.get('user_name')  # assuming user is logged in with user_name
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        action = request.form['action']
        data = {
            'email': request.form['email'],
            'password': request.form['password'],
            'age': request.form['age'],
            'phone_no': request.form['phone_no'],
            'city': request.form['city'],
            'door_no': request.form['door_no'],
            'pincode': request.form['pincode'],
            'state': request.form['state'],
        }

        if action == 'submit':
            cursor.execute("""INSERT INTO users_details 
                              (user_name, age, phone_no, city, door_no, pincode, state, email, password)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                           (user_name, data['age'], data['phone_no'], data['city'],
                            data['door_no'], data['pincode'], data['state'],
                            data['email'], data['password']))
            mysql.connection.commit()
            msg = "Details submitted successfully."
            return redirect(url_for('dashboard'))

        elif action == 'edit':
            cursor.execute("""UPDATE users_details 
                              SET age=%s, phone_no=%s, city=%s, door_no=%s, 
                                  pincode=%s, state=%s, email=%s, password=%s 
                              WHERE user_name=%s""",
                           (data['age'], data['phone_no'], data['city'], data['door_no'],
                            data['pincode'], data['state'], data['email'], data['password'],
                            user_name))
            mysql.connection.commit()
            msg = "Details updated successfully."

        return render_template('user_details.html', msg=msg, **data)

    # Handle GET request
    cursor.execute("""SELECT email, password, age, phone_no, city, door_no, 
                             pincode, state FROM users_details WHERE user_name = %s""",
                   (user_name,))
    user = cursor.fetchone()
    if user:
        return render_template('user_details.html', msg='', email=user[0], password=user[1],
                               age=user[2], phone_no=user[3], city=user[4], door_no=user[5],
                               pincode=user[6], state=user[7])
    else:
        return render_template('user_details.html', msg='', email='', password='',
                               age='', phone_no='', city='', door_no='', pincode='',
                               state='')


# ----------------- ADD ACCOUNT ROUTE -----------------
@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    if 'loggedin' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    msg = ''
    if request.method == 'POST':
        account_type = request.form['account_type']
        balance = request.form['balance']
        password = request.form['password']
        phone_no = request.form['phone_no']
        user_name = session['user_name']

        # Fetch user_id using user_name
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_name = %s', (user_name,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            cursor.execute('''
                INSERT INTO account (account_type, balance, password, phone_no, user_id)
                VALUES (%s, %s, %s, %s, %s)
            ''', (account_type, balance, password, phone_no, user_id))

            mysql.connection.commit()
            msg = 'Account created successfully!'
        else:
            msg = 'User not found!'

        cursor.close()

    return render_template('add_account.html', msg=msg)


# ----------------- TRANSACTION ROUTE -----------------
from decimal import Decimal  # ✅ Import at the top of your file

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    cursor = mysql.connection.cursor()

    # ✅ Fetch accounts for dropdown (include name if needed)
    cursor.execute("SELECT account_id FROM account")
    accounts = cursor.fetchall()

    # ✅ Fetch users for dropdown
    cursor.execute("SELECT user_id, user_name FROM users")
    users = cursor.fetchall()

    transactions = []
    selected_account_id = None

    if request.method == 'POST':
        account_id = int(request.form['account_id'])
        transaction_type = request.form['transaction_type']
        amount = Decimal(request.form['amount'])  # ✅ Convert to Decimal
        description = request.form['description']
        user_id = int(request.form['user_id'])  # ✅ Get user_id from form

        # ✅ Fetch current balance from the account table
        cursor.execute("SELECT balance FROM account WHERE account_id = %s", (account_id,))
        result = cursor.fetchone()
        balance = result[0] if result else Decimal('0.00')  # old balance

        # ✅ Calculate new total_balance
        if transaction_type == 'credit':
            total_balance = balance + amount
        else:
            total_balance = balance - amount

        # ✅ Insert transaction with old balance snapshot
        cursor.execute("""
            INSERT INTO transaction (
                transaction_type, date, amount, total_balance, description, user_id, account_id, balance
            )
            VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s)
        """, (
            transaction_type,
            amount,
            total_balance,
            description,
            user_id,
            account_id,
            balance
        ))

        # ✅ Update account's new balance
        cursor.execute("UPDATE account SET balance = %s WHERE account_id = %s", (total_balance, account_id))

        mysql.connection.commit()

        selected_account_id = account_id

    # ✅ Fetch all transactions with user_id for selected account
    if selected_account_id:
        cursor.execute("""
            SELECT transaction_id, transaction_type, amount, description, date, user_id
            FROM transaction
            WHERE account_id = %s
            ORDER BY date DESC
        """, (selected_account_id,))
        transactions = cursor.fetchall()

    return render_template("add_transaction.html",
                           accounts=accounts,
                           users=users,
                           transactions=transactions,
                           selected_account_id=selected_account_id)

# --------------View Profile -----------------------
@app.route('/view_profile')
def view_profile():
    user_name = session.get('user_name')
    cursor = mysql.connection.cursor()

    cursor.execute("""SELECT email, password, age, phone_no, city, door_no, pincode, state 
                      FROM users_details WHERE user_name = %s""", (user_name,))
    user = cursor.fetchone()

    if user:
        return render_template('View_profile.html',
                               user_name=user_name,
                               email=user[0], password=user[1], age=user[2],
                               phone_no=user[3], city=user[4], door_no=user[5],
                               pincode=user[6], state=user[7])
    else:
        return "No profile details found."



#------------------Categories------------------
@app.route('/category', methods=['GET', 'POST'])
def category():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        category_id = request.form['category_id']
        category_name = request.form['category_name']
        
        cursor.execute("INSERT INTO category (category_id, category_name) VALUES (%s, %s)", 
                       (category_id, category_name))
        mysql.connection.commit()

    cursor.execute("SELECT category_id, category_name FROM category")
    categories = cursor.fetchall()
    cursor.close()
    
    return render_template('category.html', categories=categories)

# Dummy routes for navigation (replace with real routes)

def add_transaction():
    return "<h2>Add Transaction Page (add_transaction)</h2>"
def Budget():
    return "<h2>Budget Page (Budget)</h2>"



#-----------------Budget----------------------------
@app.route('/Budget', methods=['GET', 'POST'])
def Budget():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        start = request.form['start_date']
        end = request.form['end_date']
        amount = request.form['budget_amount']
        category_id = request.form['category_id']
        action = request.form['action']

        if action == 'add':
            cursor.execute("INSERT INTO Budget (start_date, end_date, budget_amount) VALUES (%s, %s, %s)",
                           (start, end, amount))
            mysql.connection.commit()
        elif action == 'edit':
            # You can implement edit logic here
            pass

    # Fetch dynamic data
    cursor.execute("SELECT category_id, category_name FROM Category")
    categories = cursor.fetchall()

    cursor.execute("SELECT budget_id, start_date, end_date, budget_amount FROM Budget")
    budgets = cursor.fetchall()

    return render_template("Budget.html", categories=categories, budgets=budgets)



@app.route('/savings_goals', methods=['GET', 'POST'])
def savings_goals():
    if request.method == 'POST':
        goal_name = request.form['goal_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        target_amount = request.form['target_amount']
        current_savings = request.form['current_savings']
        user_id = request.form['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO savings_goals (goal_name, start_date, end_date, target_amount, current_savings, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (goal_name, start_date, end_date, target_amount, current_savings, user_id))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('savings_goals'))  # reload the page or show success

    return render_template('savings_goals.html')


@app.route('/view_goals')
def view_goals():
    user_name = session.get('user_name')

    # Get user_id based on user_name
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_name = %s", (user_name,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]

        # Fetch savings goals for this user
        cursor.execute("""SELECT goal_name, start_date, end_date, target_amount, current_savings
                          FROM savings_goals WHERE user_id = %s""", (user_id,))
        goals = cursor.fetchall()

        return render_template('view_goals.html', goals=goals)
    else:
        return "No user found or you are not logged in."
    
#----------------Bill-----------
@app.route('/Bill', methods=['GET', 'POST'])
def Bill():
    selected_bill = None
    if request.method == 'POST':
        user_id = request.form['userId']
        bill_type = request.form['billType']
        due_date = request.form['dueDate']
        amount = request.form['amount']
        status = request.form['status']

        try:
            cursor = mysql.connection.cursor()
            
            # Check if user ID exists in users table
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()

            if user:
                cursor.execute("""
                    INSERT INTO bill (user_id, bill_type, due_date, amount, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, bill_type, due_date, amount, status))
                mysql.connection.commit()

                # Get the last inserted bill (without user_id for preview)
                cursor.execute("""
                    SELECT bill_id, bill_type, due_date, amount, status
                    FROM bill
                    ORDER BY bill_id DESC
                    LIMIT 1
                """)
                selected_bill = cursor.fetchone()
            else:
                return "User ID does not exist in the system."

        except MySQL.Error as e:
            return f"Database error: {e}"
        finally:
            cursor.close()
            

    return render_template('Bill.html', selected_bill=selected_bill)

# ----------------- RUN FLASK APP -----------------
if __name__ == '__main__':
    app.run(debug=True)
