from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import datetime
import re

app = Flask(__name__)
app.secret_key = 'Alfie'
mysql = connectToMySQL('wall_users')
now = datetime.datetime.now()
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

@app.route('/')
def renderIndex():
    if 'logged_in' in session and 'user_id' in session and session['logged_in'] == True:
        #Getting the user_id
        data = {
                'user_id': session['user_id'],
            }
        #Getting the amount of messages received by the user
        n_received_query = "SELECT COUNT(message) FROM messages WHERE receiver_id LIKE %(user_id)s"
        n_received_messages = mysql.query_db(n_received_query,data)
        session['n_received_messages'] = n_received_messages[0]['COUNT(message)']

        #Getting actual messages received
        received_query = "SELECT messages.id,messages.message,messages.created_at,regusers.first_name as sender_name FROM messages JOIN regusers ON messages.sender_id=regusers.id WHERE receiver_id LIKE %(user_id)s;"
        received_messages = mysql.query_db(received_query,data)

        #Getting the amount of sent messages
        sent_query = "SELECT COUNT(message) FROM messages WHERE sender_id LIKE %(user_id)s"
        n_sent_messages = mysql.query_db(sent_query,data)
        session['n_sent_messages'] = n_sent_messages[0]['COUNT(message)']

        #Getting all other users
        all_users_query = "SELECT id,first_name FROM regusers WHERE id NOT LIKE %(user_id)s;"
        all_users = mysql.query_db(all_users_query,data)

        #getting user_level
        user_level_query = "SELECT user_level FROM regusers WHERE id LIKE %(user_id)s;"
        user_level = mysql.query_db(user_level_query,data)[0]['user_level']

        if user_level == 9:
            #This is an admin user
            #Getting all users to create admin table
            total_users_query = "SELECT id,first_name,email,user_level FROM regusers;"
            total_users = mysql.query_db(total_users_query)

            return render_template("admin.html",received_messages=received_messages,all_users=all_users,total_users=total_users)
        else:
            return render_template("index.html",received_messages=received_messages,all_users=all_users)
    else:
        return render_template("login_and_registration.html")

@app.route('/process_registration',methods=['POST'])
def procRegistration():
    #Getting current emails in the database,for comparison
    current_emails = mysql.query_db("SELECT email FROM regusers")

    #first_name should be longer than 2 characters and all letters:
    if len(request.form['first_name']) < 2:
        flash("First Name must be at least 2 characters","name_error")
    elif not request.form['first_name'].isalpha():
        flash("First Name must have only letters","name_error")
    else:
        session['first_name'] = request.form['first_name']
    #last_name should be longer than 2 characters and all letters
    if len(request.form['last_name']) < 2:
        flash("Last Name must be at least 2 characters","lname_error")
    elif not request.form['last_name'].isalpha():
        flash("Last Name must be letters only","lname_error")
    else:
        session['last_name'] = request.form['last_name']
    #email address must be new and valid format
    for item in current_emails:
        if request.form['email'] == item['email']:
            flash("Email already in list!","email_error")
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", "email_error")
    else:
        session['email'] = request.form['email']
    #Password must be at least 8 characters; must match confirm password
    if len(request.form['password']) < 8:
        flash("Password must have at least 8 characters","password_error")
    elif request.form['confirm_password'] != request.form['password']:
        flash("Confirm password must match original password","cpassword_error")

    if '_flashes' in session.keys():
        return redirect("/")
    else:
        #Hashing password and adding it to session
        session['password'] = bcrypt.generate_password_hash(request.form['password'])
        session['logged_in'] = True
        data = {
                'first_name': session['first_name'],
                'last_name': session['last_name'],
                'email': session['email'],
                'password': session['password'],
                'created_at': now,
                'updated_at': now
            }
        query = "INSERT INTO regusers (first_name,last_name,email,password_hash,created_at,updated_at) VALUES (%(first_name)s,%(last_name)s,%(email)s,%(password)s,%(created_at)s,%(updated_at)s);"
        mysql.query_db(query, data)
        print(session)
        flash("You've been sucessfully registered!","sucess")
        return redirect('/')

@app.route('/login',methods=['POST'])
def logIn():
    #Getting info from the forms
    provided_email = request.form['email']
    if len(request.form['email']) < 1:
        flash("Please enter a valid email address","login_error")
    #Missing email format validation
    provided_password = request.form['password']
    if len(request.form['password']) < 1:
        flash("Please enter a valid password","login_error")

    if '_flashes' in session.keys():
        return redirect("/")
    else:
        #Fetching current emails and passwords
        current_data = mysql.query_db("SELECT id,email,first_name,password_hash FROM regusers")
        print(current_data)

        #Checking if email is in the current data
        for item in current_data:
            if item['email'] == provided_email:
                if bcrypt.check_password_hash(item['password_hash'], provided_password):
                    session.clear()
                    session['logged_in'] = True
                    session['user_id'] = item['id']
                    session['email'] = item['email']
                    session['name'] = item['first_name']
                    print(session)
                    return redirect('/')
            
        flash("Issues with email or password","login_error")
        return redirect('/')

@app.route('/send_message',methods=['POST'])
def sendMessage():
    data = {
            'receiver_id': request.form['receiver_id'],
            'message': request.form['message'],
            'user_id': session['user_id']
        }
    send_query = "INSERT INTO messages (message,sender_id,receiver_id,created_at,updated_at) VALUES (%(message)s,%(user_id)s,%(receiver_id)s,now(),now());"
    mysql.query_db(send_query,data)
    return redirect('/')

@app.route('/delete_message/<message_id>')
def deleteMessage(message_id):
    #Getting specific message to be deleted and its attributes
    data = {
        'message_id': message_id,
        }
    query = "SELECT receiver_id FROM messages WHERE id LIKE %(message_id)s;"
    r_msg_to_be_deleted = mysql.query_db(query,data)[0]['receiver_id']
    if r_msg_to_be_deleted == session['user_id']:
        print("match user id and receiver id. about to delete message")
        delete_data = {
        'message_id': message_id,
        }
        delete_query = "DELETE FROM messages WHERE id LIKE %(message_id)s;"
        mysql.query_db(delete_query,delete_data)
        return redirect('/')
    else:
        return "you're not allowed to delete this message"

@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect('/')

@app.route('/remove_user/<user_id>')
def remove_user(user_id):
    user_delete_data = {
        'user_id': user_id,
        }
    user_delete_query = "DELETE FROM regusers WHERE id LIKE %(user_id)s"
    mysql.query_db(user_delete_query,user_delete_data)
    return redirect('/')

@app.route('/remove_admin/<user_id>')
def remove_admin(user_id):
    admin_remove_data = {
        'user_id': user_id,
        }
    admin_remove_query = "UPDATE regusers SET user_level=1 WHERE id LIKE %(user_id)s"
    mysql.query_db(admin_remove_query,admin_remove_data)
    return redirect('/')

@app.route('/create_admin/<user_id>')
def create_admin(user_id):
    admin_create_data = {
        'user_id': user_id,
        }
    admin_create_query = "UPDATE regusers SET user_level=9 WHERE id LIKE %(user_id)s"
    mysql.query_db(admin_create_query,admin_create_data)
    return redirect('/')

if __name__=="__main__":
    app.run(debug=True)