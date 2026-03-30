from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
import os

 

mydb = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=int(os.getenv("MYSQLPORT"))
)
cursor = mydb.cursor()

app = Flask(__name__)
app.secret_key = 'actnow_secret_key_2025'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────────────────
# INDEX & GENERAL
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/loginpage")
def loginpage():
    return render_template('login.html')

@app.route("/about_contact")
def about_contact():
    return render_template('about_contact.html')

@app.route("/inquiries", methods=['GET', 'POST'])
def inquiries():
    if request.method == 'GET':
        name    = request.args.get('name')
        email   = request.args.get('email')
        message = request.args.get('message')
        cursor.execute("INSERT INTO inquiries(full_name,email,message) VALUES(%s,%s,%s)", (name, email, message))
        mydb.commit()
    return render_template('index.html')


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

@app.route("/register_page", methods=['POST'])
def register_page():
    name     = request.form['name']
    email    = request.form['email']
    password = request.form['password']
    role     = request.form['role']

    if role == 'Volunteer':
        cursor.execute("INSERT INTO vol_register(full_name,email,password,role) VALUES(%s,%s,%s,%s)", (name, email, password, role))
    elif role == 'Organizer':
        cursor.execute("INSERT INTO org_register(full_name,email,password,role) VALUES(%s,%s,%s,%s)", (name, email, password, role))
    mydb.commit()
    return render_template('login.html')


@app.route("/login", methods=['POST'])
def login():
    email    = request.form['email']
    password = request.form['password']
    role     = request.form['role']

    if role == 'Volunteer':
        cursor.execute("SELECT * FROM vol_register WHERE email=%s AND password=%s", (email, password))
        result = cursor.fetchone()
        if result:
            session['role']       = 'Volunteer'
            session['user_id']    = result[0]
            session['user_name']  = result[1]
            session['user_email'] = result[2]
            return redirect(url_for('index'))
        return redirect(url_for('loginpage') + '?error=1')  # ← changed

    elif role == 'Organizer':
        cursor.execute("SELECT * FROM org_register WHERE email=%s AND password=%s", (email, password))
        result = cursor.fetchone()
        if result:
            session['role']      = 'Organizer'
            session['org_id']    = result[0]
            session['org_name']  = result[1]
            session['org_email'] = result[2]
            return redirect(url_for('organizer_dashboard'))
        return redirect(url_for('loginpage') + '?error=1')  # ← changed

    elif role == 'Admin':
        if email == "admin@gmail.com" and password == "123":
            session['role'] = 'Admin'
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('loginpage') + '?error=1')  # ← changed

    return redirect(url_for('loginpage') + '?error=1')      # ← changed

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─────────────────────────────────────────
# CAMPAIGNS (PUBLIC)
# ─────────────────────────────────────────

@app.route("/campaigns")
def campaigns():
    cursor.execute("SELECT * FROM create_campaign")
    result = cursor.fetchall()
    return render_template('campaigns.html', result=result)

@app.route("/campaigns_search", methods=['GET'])
def campaign_search():
    search = request.args.get('search', '')
    state  = request.args.get('state', '')
    status = request.args.get('status', '')

    query  = "SELECT * FROM create_campaign WHERE 1=1"
    params = []

    if search:
        query += " AND (title LIKE %s OR state LIKE %s OR district LIKE %s)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    if state:
        query += " AND state = %s"
        params.append(state)

    if status:
        query += " AND status = %s"
        params.append(status)

    cursor.execute(query, params)
    result = cursor.fetchall()
    return render_template('campaigns.html', result=result)


# ─────────────────────────────────────────
# VOLUNTEER
# ─────────────────────────────────────────

@app.route("/reg_campaign/<info>")
def reg_campaign(info):
    cursor.execute("SELECT * FROM create_campaign WHERE id=%s", (info,))
    result = cursor.fetchall()
    return render_template('reg_campaign.html', result=result)

@app.route("/register_volunteer", methods=['POST'])
def register_volunteer():
    title     = request.form['title']
    organizer = request.form['organizer']
    address   = request.form['address']
    date      = request.form['date']
    full_name = request.form['full_name']
    email     = request.form['email']
    age       = request.form['age']
    phone_no  = request.form['phone_no']
    cursor.execute(
        "INSERT INTO campaign_reg(title,organizer,address,date,full_name,email,age,phone_no) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
        (title, organizer, address, date, full_name, email, age, phone_no)
    )
    mydb.commit()
    cursor.execute("SELECT * FROM campaign_reg")
    result = cursor.fetchall()
    return render_template('volunteer_registered.html', result=result)

@app.route("/volunteer_registration")
def volunteer_registration():
    if 'user_id' not in session:
        return redirect(url_for('loginpage'))
    user_email = session.get('user_email', '')
    cursor.execute("SELECT * FROM campaign_reg WHERE email=%s", (user_email,))
    result = cursor.fetchall()
    return render_template('volunteer_registered.html', result=result)


# ─────────────────────────────────────────
# ORGANIZER
# ─────────────────────────────────────────

@app.route("/organizer_dashboard")
def organizer_dashboard():
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))
    org_name  = session.get('org_name', 'Organizer')
    org_email = session.get('org_email', '')
    cursor.execute("SELECT COUNT(*) FROM create_campaign WHERE organizer_email=%s", (org_email,))
    campaign_count = cursor.fetchone()[0]
    return render_template('organizer_dashboard.html',
                           org_name=org_name,
                           org_email=org_email,
                           campaign_count=campaign_count)


@app.route("/create_campaigns")
def create_campaigns():
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))
    return render_template('create_campaigns.html')


@app.route("/create_newcampaign", methods=['POST'])
def create_new_campaign():
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))

    title       = request.form['title']
    organizer   = request.form['organizer']
    description = request.form['description']
    address     = request.form['address']
    state       = request.form['state']
    district    = request.form['district']
    date        = request.form['date']
    status      = request.form.get('status', 'Active')
    org_email   = session.get('org_email', '')

    file = request.files['image']
    if file and file.filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)
        image_url = f'static/uploads/{file.filename}'
    else:
        image_url = None

    cursor.execute(
        "INSERT INTO create_campaign(title,organizer,description,address,state,district,date,image,organizer_email,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (title, organizer, description, address, state, district, date, image_url, org_email, status)
    )
    mydb.commit()
    return redirect(url_for('manage_campaigns'))


@app.route("/manage_campaigns")
def manage_campaigns():
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))
    org_email = session.get('org_email', '')
    cursor.execute("SELECT * FROM create_campaign WHERE organizer_email=%s", (org_email,))
    result = cursor.fetchall()
    return render_template('manage_campaigns.html', result=result)


@app.route("/campaign_volunteers/<int:campaign_id>")
def campaign_volunteers(campaign_id):
    if 'org_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    cursor.execute("SELECT title FROM create_campaign WHERE id=%s", (campaign_id,))
    campaign = cursor.fetchone()
    if not campaign:
        return jsonify({"error": "Not found"}), 404
    cursor.execute(
        "SELECT full_name, email, age, phone_no FROM campaign_reg WHERE title=%s",
        (campaign[0],)
    )
    volunteers = cursor.fetchall()
    vol_list = [{"name": v[0], "email": v[1], "age": v[2], "phone": v[3]} for v in volunteers]
    return jsonify({"campaign_title": campaign[0], "volunteers": vol_list, "count": len(vol_list)})


@app.route("/o_edit/<info>")
def o_edit(info):
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))
    cursor.execute("SELECT * FROM create_campaign WHERE id=%s", (info,))
    result = cursor.fetchall()
    return render_template('edit.html', result=result)


@app.route('/edited/<info>', methods=['POST'])
def edited(info):
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))

    title       = request.form['title']
    organizer   = request.form['organizer']
    description = request.form['description']
    address     = request.form['address']
    state       = request.form['state']
    district    = request.form['district']
    date        = request.form['date']
    status      = request.form.get('status', 'Active')

    file = request.files['image']
    if file and file.filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)
        image_url = f'static/uploads/{file.filename}'
    else:
        cursor.execute("SELECT image FROM create_campaign WHERE id=%s", (info,))
        old = cursor.fetchone()
        image_url = old[0] if old else None

    cursor.execute(
        "UPDATE create_campaign SET title=%s,organizer=%s,description=%s,address=%s,state=%s,district=%s,date=%s,image=%s,status=%s WHERE id=%s",
        (title, organizer, description, address, state, district, date, image_url, status, info)
    )
    mydb.commit()
    return redirect(url_for('manage_campaigns'))


@app.route("/o_delete/<info>")
def o_delete(info):
    if 'org_id' not in session:
        return redirect(url_for('loginpage'))
    cursor.execute("DELETE FROM create_campaign WHERE id=%s", (info,))
    mydb.commit()
    return redirect(url_for('manage_campaigns'))


# ─────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────

@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get('role') != 'Admin':
        return redirect(url_for('loginpage'))

    cursor.execute("SELECT COUNT(*) FROM vol_register")
    vol_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM org_register")
    org_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM create_campaign")
    campaign_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inquiries")
    inquiry_count = cursor.fetchone()[0]

    return render_template('admin_dashboard.html',
                           vol_count=vol_count,
                           org_count=org_count,
                           campaign_count=campaign_count,
                           inquiry_count=inquiry_count)

@app.route("/view_volunteer")
def manage_volunteer():
    cursor.execute("SELECT * FROM vol_register")
    result = cursor.fetchall()
    return render_template('view_volunteer.html', result=result)

@app.route("/view_organizer")
def manage_organizer():
    cursor.execute("SELECT * FROM org_register")
    result = cursor.fetchall()
    return render_template('view_organizer.html', result=result)

@app.route("/view_campaigns")
def view_campaigns():
    cursor.execute("SELECT * FROM create_campaign")
    result = cursor.fetchall()
    return render_template('view_campaigns.html', result=result)

@app.route("/view_inquiries")
def view_inquiries():
    cursor.execute("SELECT * FROM inquiries")
    result = cursor.fetchall()
    return render_template('view_inquiries.html', result=result)

@app.route("/a_delete/<info>")
def a_delete(info):
    cursor.execute("DELETE FROM create_campaign WHERE id=%s", (info,))
    mydb.commit()
    return redirect(url_for('view_campaigns'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
