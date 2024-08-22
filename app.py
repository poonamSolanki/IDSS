import bcrypt
from flask import Flask, render_template, redirect, url_for, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, RadioField, SelectField, TextAreaField, DecimalField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, ValidationError, Regexp, Length
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root@123'
app.config['MYSQL_DB'] = 'user_management'
app.secret_key = 'abcd'

mysql = MySQL(app)

# Define WTForms for registration, login, update, and investment category
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired(), Regexp(r'^\d{10}$', message="Phone number must be 10 digits.")])
    dob = DateField("Date of Birth", validators=[DataRequired()])
    state = StringField("State", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    user_type = RadioField("Register as:", choices=[('user', 'User'), ('admin', 'Admin')], default='user', validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        cursor = mysql.connection.cursor()
        if self.user_type.data == 'user':
            cursor.execute("SELECT * FROM user WHERE email=%s", (field.data,))
        
        else:
            cursor.execute("SELECT * FROM admindetail WHERE email=%s", (field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class UpdateForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password")  # Optional: Include if you want to update passwords
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired()])
    dob = DateField("Date of Birth", validators=[DataRequired()])
    state = StringField("State", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    user_type = RadioField("Register as:", choices=[('user', 'User'), ('admin', 'Admin')], default='user', validators=[DataRequired()])
    submit = SubmitField("Update")

class InvestmentCategoryForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class InvestmentSubcategoryForm(FlaskForm):
    investment_category = SelectField('Investment Category', coerce=int, validators=[DataRequired()])
    subcategory = StringField('Investment Subcategory', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ExpenseTypeForm(FlaskForm):
    expense_type_title = StringField('Expense Type Title', validators=[DataRequired()])
    expense_type_description = TextAreaField('Expense Type Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ExpenseFactorForm(FlaskForm):
    factorname = StringField('Factor Name', validators=[DataRequired()])
    factordescription = TextAreaField('Factor Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddExpenseForm(FlaskForm):
    expensetypeid = SelectField('Expense Type', coerce=int, validators=[DataRequired()])
    expensefactorid = SelectField('Expense Factor', coerce=int, validators=[DataRequired()])
    expensetitle = StringField('Expense Title', validators=[DataRequired()])
    expensedetail = TextAreaField('Expense Detail', validators=[DataRequired()])
    submit = SubmitField('Add Expense')
class InvestmentProductForm(FlaskForm):
    subcategory = SelectField('Investment Subcategory', validators=[DataRequired()], coerce=int)
    product_name = StringField('Product Name', validators=[DataRequired()])
    details = TextAreaField('Details', validators=[DataRequired()])
    enteredon = DateField('Entered On', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('investment product')

class ProductExpenseForm(FlaskForm):
    expense = SelectField('Expense', choices=[], coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    submit = SubmitField('Add Expense Detail')

class ProductRevenueForm(FlaskForm):
    revenue = SelectField('Revenue', coerce=int)
    amount = DecimalField('Amount', validators=[DataRequired()])

class AddRevenueForm(FlaskForm):
    subcategory = SelectField('Subcategory', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired(), Length(min=2, max=255)])
    submit = SubmitField('Add Revenue')
class EditRevenueForm(FlaskForm):
    revenue_id = HiddenField('Revenue ID')
    subcategory = SelectField('Investment Subcategory', coerce=int, validators=[DataRequired()])
    revenue = StringField('Revenue', validators=[DataRequired(), Length(min=1, max=255)])
    submit = SubmitField('Update')



    # Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    return render_template('index.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        phone = form.phone.data
        dob = form.dob.data
        state = form.state.data
        city = form.city.data
        user_type = form.user_type.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor = mysql.connection.cursor()
        
        if user_type == 'admin':
            cursor.execute("INSERT INTO admindetail (username, password, email, phone, dob, state, city) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (username, hashed_password, email, phone, dob, state, city))
        
        else:
            cursor.execute("INSERT INTO user (username, password, email, phone, dob, state, city) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (username, hashed_password, email, phone, dob, state, city))

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        # Check if the email exists in the user table
        cursor.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            # Verify the password for user
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['user_id'] = user[0]
                session['login_type'] = 'user'
                cursor.close()
                return redirect(url_for('investment_product_detailing'))  # Redirect to the appropriate user dashboard

        

        # Check if the email exists in the admin table
        cursor.execute("SELECT * FROM admindetail WHERE email=%s", (email,))
        admin = cursor.fetchone()
        cursor.close()

        if admin:
            # Verify the password for admin
            if bcrypt.checkpw(password.encode('utf-8'), admin[2].encode('utf-8')):
                session['user_id'] = admin[0]
                session['login_type'] = 'admin'
                return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard

        flash("Login failed. Please check your email and password")
        return redirect(url_for('login'))

    return render_template('login.html', form=form)



@app.route('/dashboard')
def dashboard():
    cursor = mysql.connection.cursor()

    # Fetch data for the user
    if 'user_id' in session and session.get('login_type') == 'user':
        user_id = session['user_id']
        cursor.execute("SELECT id, username FROM user WHERE id=%s", (user_id,))
        user = cursor.fetchone()
    else:
        user = None

    # Fetch data for the table
    cursor.execute("""
        SELECT ic.category AS category, isc.name AS subcategory, ipe.amount AS expense_amount, ipr.amount AS revenue_amount
        FROM investmentcatg ic
        JOIN investmentsubcatg isc ON ic.Investementcatgid = isc.category_id
        JOIN InvestmentProduct ip ON isc.id= ip.Investmentsubcatgid
        LEFT JOIN InvstProductExpense ipe ON ip.Ipid = ipe.Ipid
        LEFT JOIN InvstProductRevenue ipr ON ip.Ipid = ipr.Ipid
    """)
    data = cursor.fetchall()
    cursor.close()

    return render_template('dashboard.html', user=user, data=data)


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' in session and session.get('login_type') == 'user':
        user_id = session['user_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if request.method == 'POST':
            # Add logic to update user profile here
            pass

        if user:
            return render_template('update_profile.html', user=user)
        else:
            flash('User not found.')

    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('login_type', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

# -----------------------------------------------

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session.get('login_type') == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        cursor.close()

        return render_template('admin_dashboard.html', users=users)
    flash('Access denied. Please log in as an admin.')
    return redirect(url_for('login'))



@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    # Check if user is logged in as admin
    if 'user_id' not in session or session.get('login_type') != 'admin':
        flash('Access denied.')
        return redirect(url_for('login'))

    form = UpdateForm()

    # Handle POST request (update user details)
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        dob = form.dob.data
        state = form.state.data
        city = form.city.data
        user_type = form.user_type.data

        # Update user details in the database
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE user SET username=%s, email=%s, phone=%s, dob=%s, state=%s, city=%s WHERE id=%s",
                       (name, email, phone, dob, state, city, user_id))
        mysql.connection.commit()
        cursor.close()

        flash('User details have been updated successfully.')
        return redirect(url_for('admin_dashboard'))

    # Fetch user details from database for GET request
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        # Populate form fields with user data
        form.name.data = user[1]
        form.email.data = user[3]
        form.phone.data = user[4]
        form.dob.data = user[5]
        form.state.data = user[6]
        form.city.data = user[7]

        return render_template('update.html', form=form, user=user)
    else:
        flash('User not found.')
        return redirect(url_for('admin_dashboard'))

@app.route('/investment_category', methods=['GET', 'POST'])
def investment_category():
    form = InvestmentCategoryForm()
    if form.validate_on_submit():
        category = form.category.data
        description = form.description.data

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO investmentcatg (Category, Description) VALUES (%s, %s)", (category, description))
        mysql.connection.commit()
        cursor.close()
        
        flash('Investment category added successfully.')
        return redirect(url_for('investment_dashboard'))

    return render_template('investment_category.html', form=form)


@app.route('/investment_dashboard')
def investment_dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM investmentcatg")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM investmentsubcatg")
    subcategories = cursor.fetchall()
    
    cursor.close()

    return render_template('investment_dashboard.html', categories=categories, subcategories=subcategories)


@app.route('/update_category/<int:category_id>', methods=['GET', 'POST'])
def update_category(category_id):
    form = InvestmentCategoryForm()
    cursor = mysql.connection.cursor()
    
    if form.validate_on_submit():
        category = form.category.data
        description = form.description.data
        cursor.execute("UPDATE investmentcatg SET Category=%s, Description=%s WHERE Investementcatgid=%s", (category, description, category_id))
        mysql.connection.commit()
        cursor.close()
        flash('Investment category updated successfully.')
        return redirect(url_for('investment_dashboard'))
    
    cursor.execute("SELECT * FROM investmentcatg WHERE Investementcatgid=%s", (category_id,))
    category = cursor.fetchone()
    cursor.close()
    
    if category:
        form.category.data = category[1]
        form.description.data = category[2]
    
    return render_template('update_category.html', form=form)



@app.route('/update_subcategory/<int:subcategory_id>', methods=['GET', 'POST'])
def update_subcategory(subcategory_id):
    form = InvestmentSubcategoryForm()
    cursor = mysql.connection.cursor()
    
    # Fetch categories first and set the choices for the form field
    cursor.execute("SELECT Investementcatgid, Category FROM investmentcatg")
    categories = cursor.fetchall()
    form.investment_category.choices = [(cat[0], cat[1]) for cat in categories]

    # Fetch the existing subcategory data
    cursor.execute("SELECT * FROM investmentsubcatg WHERE id=%s", (subcategory_id,))
    subcategory = cursor.fetchone()
    cursor.close()

    if form.validate_on_submit():
        investment_category_id = form.investment_category.data
        subcategory_name = form.subcategory.data
        description = form.description.data
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE investmentsubcatg SET category_id=%s, name=%s, Description=%s WHERE id=%s", 
                       (investment_category_id, subcategory_name, description, subcategory_id))
        mysql.connection.commit()
        cursor.close()
        flash('Investment subcategory updated successfully.')
        return redirect(url_for('investment_dashboard'))

    # Prepopulate the form with existing subcategory data
    if subcategory:
        form.investment_category.data = subcategory[1]  # Assuming category_id is the second field
        form.subcategory.data = subcategory[2]          # Assuming name is the third field
        form.description.data = subcategory[3]          # Assuming Description is the fourth field

    return render_template('update_subcategory.html', form=form)


@app.route('/investment_subcategory', methods=['GET', 'POST'])
def investment_subcategory():
    form = InvestmentSubcategoryForm()
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT Investementcatgid, Category FROM investmentcatg")
    categories = cursor.fetchall()
    cursor.close()

    form.investment_category.choices = [(cat[0], cat[1]) for cat in categories]

    if form.validate_on_submit():
        investment_category_id = form.investment_category.data
        subcategory = form.subcategory.data
        description = form.description.data

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO investmentsubcatg (category_id, name, Description) VALUES (%s, %s, %s)",
                       (investment_category_id, subcategory, description))
        mysql.connection.commit()
        cursor.close()

        flash('Investment subcategory added successfully.')
        return redirect(url_for('investment_dashboard'))

    return render_template('investment_subcategory.html', form=form)


@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM investmentsubcatg WHERE category_id=%s", (category_id,))
    cursor.execute("DELETE FROM investmentcatg WHERE Investementcatgid=%s", (category_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Investment category deleted successfully.')
    return redirect(url_for('investment_dashboard'))


@app.route('/delete_subcategory/<int:subcategory_id>', methods=['POST'])
def delete_subcategory(subcategory_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM investmentsubcatg WHERE id=%s", (subcategory_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Investment subcategory deleted successfully.')
    return redirect(url_for('investment_dashboard'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Check if user is logged in as admin
    if 'user_id' not in session or session.get('login_type') != 'admin':
        flash('Access denied.')
        return redirect(url_for('login'))

    # Delete the user from the database
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cursor.close()

    flash('User has been deleted successfully.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin_dashboard_page')
def admin_dashboard_page():
    # Assuming you have a list of users to display in the admin dashboard
    users = [
        (1, 'user1', 'user1@example.com'),
        (2, 'user2', 'user2@example.com'),
        (3, 'user3', 'user3@example.com')
    ]
    return render_template('admin_dashboard.html', users=users)

@app.route('/expense_dashboard')
def expense_dashboard():
    cursor = mysql.connection.cursor()
    
    # Fetch data for display
    cursor.execute("SELECT * FROM expense_type")
    expense_type = cursor.fetchall()
    
    cursor.execute("SELECT * FROM expense_factors")
    expense_factors = cursor.fetchall()

    cursor.execute("""
        SELECT e.Expenseid, et.expense_type_title, ef.factorname, e.expensetitle, e.expensedetail 
        FROM expenses e 
        JOIN expense_type et ON e.Expensetypeid = et.expense_type_id 
        JOIN expense_factors ef ON e.Expensefactorid = ef.factorid

    """)
    expenses = cursor.fetchall()
    
    cursor.close()
    
    return render_template('expense_dashboard.html', expense_type=expense_type, expense_factors=expense_factors,expenses=expenses)



@app.route('/add_expense_type', methods=['GET', 'POST'])
def add_expense_type():
    form = ExpenseTypeForm()
    if form.validate_on_submit():
        expense_type_title = form.expense_type_title.data
        expense_type_description = form.expense_type_description.data

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO expense_type (expense_type_title, expense_type_description) VALUES (%s, %s)",
                       (expense_type_title, expense_type_description))
        mysql.connection.commit()
        cursor.close()

        flash('Expense type added successfully.')
        return redirect(url_for('expense_dashboard'))

    return render_template('add_expense_type.html', form=form)



@app.route('/add_expense_factors', methods=['GET', 'POST'])
def add_expense_factors():
    form = ExpenseFactorForm()
    if form.validate_on_submit():
        factorname = form.factorname.data
        factordescription = form.factordescription.data

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO expense_factors (factorname, factordescription) VALUES (%s, %s)",
                       (factorname, factordescription))
        mysql.connection.commit()
        cursor.close()

        flash('Expense factor added successfully.')
        return redirect(url_for('expense_dashboard'))

    return render_template('add_expense_factors.html', form=form)


@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    form = AddExpenseForm()

    # Populate SelectField choices from database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM expense_type")
    form.expensetypeid.choices = [(row[0], row[1]) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM expense_factors")
    form.expensefactorid.choices = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.close()

    if form.validate_on_submit():
        expense_type_id = form.expensetypeid.data
        factor_id = form.expensefactorid.data
        expensetitle = form.expensetitle.data
        expensedetail = form.expensedetail.data

        # Insert into expenses table
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO expenses (Expensetypeid, Expensefactorid, Expensetitle, Expensedetail) VALUES (%s, %s, %s, %s)",
                       (expense_type_id, factor_id, expensetitle, expensedetail))
        mysql.connection.commit()
        cursor.close()

        flash('Expense added successfully.', 'success')
        return redirect(url_for('expense_dashboard'))

    return render_template('add_expense.html', form=form)



@app.route('/investment_product_detailing', methods=['GET', 'POST'])
def investment_product_detailing():
    product_form = InvestmentProductForm()
    expense_form = ProductExpenseForm()
    revenue_form = ProductRevenueForm()

    cursor = mysql.connection.cursor()

    # Fetch subcategories for the dropdown
    cursor.execute("SELECT id, name FROM investmentsubcatg")
    subcategories = cursor.fetchall()
    subcategories = [{'id': subcat[0], 'name': subcat[1]} for subcat in subcategories]
    product_form.subcategory.choices = [(subcat['id'], subcat['name']) for subcat in subcategories]

    # Fetch expenses for the dropdown
    cursor.execute("SELECT expenseid, expensedetail FROM expenses")
    expenses = cursor.fetchall()
    expenses = [{'id': exp[0], 'detail': exp[1]} for exp in expenses]
    expense_form.expense.choices = [(exp['id'], exp['detail']) for exp in expenses]

    # Fetch revenues for the dropdown
    cursor.execute("SELECT revenuetypeid, revenue FROM revenuetype")
    revenues = cursor.fetchall()
    revenues = [{'id': rev[0], 'name': rev[1]} for rev in revenues]
    revenue_form.revenue.choices = [(rev['id'], rev['name']) for rev in revenues]

    ipid = None

    if request.method == 'POST':
        if 'save_product' in request.form and product_form.validate_on_submit():
            subcategory_id = product_form.subcategory.data
            product_name = product_form.product_name.data
            details = product_form.details.data
            enteredon = product_form.enteredon.data.strftime('%Y-%m-%d')

            try:
                cursor.execute("""
                    INSERT INTO InvestmentProduct (Investmentsubcatgid, Productname, Details, Status, Enteredon)
                    VALUES (%s, %s, %s, %s, %s)
                """, (subcategory_id, product_name, details, True, enteredon))

                mysql.connection.commit()
                ipid = cursor.lastrowid
                print(f"Investment Product added with id: {ipid}")

                flash('Investment Product added successfully! Please add expenses and revenues now.', 'success')
            except Exception as e:
                mysql.connection.rollback()
                print(f"Error adding investment product: {e}")
                flash(f"Error adding investment product: {e}", 'error')

        elif 'save_expense_revenue' in request.form:
            ipid = request.form.get('ipid')
            expenses = request.form.getlist('expense[]')
            expense_amounts = request.form.getlist('amount[]')
            revenues = request.form.getlist('revenue[]')
            revenue_amounts = request.form.getlist('revenue_amount[]')

            print(f"Received IPID: {ipid}")
            print(f"Expenses: {expenses}")
            print(f"Expense Amounts: {expense_amounts}")
            print(f"Revenues: {revenues}")
            print(f"Revenue Amounts: {revenue_amounts}")

            if not ipid or not expenses or not expense_amounts or not revenues or not revenue_amounts:
                flash('Form data is missing.', 'error')
                return redirect(url_for('investment_product_detailing'))

            try:
                # Clear previous expenses and revenues
                cursor.execute("DELETE FROM InvstProductExpense WHERE Ipid = %s", (ipid,))
                cursor.execute("DELETE FROM InvstProductRevenue WHERE Ipid = %s", (ipid,))

                for expense, amount in zip(expenses, expense_amounts):
                    if amount:  # Check if amount is not empty
                        print(f"Inserting expense: Ipid={ipid}, Expenseid={expense}, Amount={amount}")
                        cursor.execute("""
                            INSERT INTO invstproductexpense (Ipid, Expenseid, Amount)
                            VALUES (%s, %s, %s)
                        """, (ipid, expense, float(amount)))  # Ensure amount is a float

                for revenue, amount in zip(revenues, revenue_amounts):
                    if amount:  # Check if amount is not empty
                        print(f"Inserting revenue: Ipid={ipid}, Revenuetypeid={revenue}, Amount={amount}")
                        cursor.execute("""
                            INSERT INTO InvstProductRevenue (Ipid, Revenuetypeid, Amount)
                            VALUES (%s, %s, %s)
                        """, (ipid, revenue, float(amount)))  # Ensure amount is a float

                mysql.connection.commit()
                flash('Product Expenses and Revenues added successfully!', 'success')
            except Exception as e:
                mysql.connection.rollback()
                print(f"Error adding product expenses and revenues: {e}")
                flash(f"Error adding product expenses and revenues: {e}", 'error')

    cursor.close()
    return render_template('investment_product_detailing.html', 
                           product_form=product_form, 
                           expense_form=expense_form, 
                           revenue_form=revenue_form, 
                           subcategories=subcategories, 
                           expenses=expenses, 
                           revenues=revenues, 
                           ipid=ipid)


@app.route('/add_revenue', methods=['GET', 'POST'])
def add_revenue():
    form = AddRevenueForm()
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name FROM investmentsubcatg")
    subcategories = cursor.fetchall()
    cursor.close()

    # Ensure subcategories is a list of tuples
    form.subcategory.choices = [(subcat[0], subcat[1]) for subcat in subcategories]

    if form.validate_on_submit():
        subcategory_id = form.subcategory.data
        description = form.description.data

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO revenuetype (investmentsubcatgid, revenue) VALUES (%s, %s)",
                (subcategory_id, description)
            )
            mysql.connection.commit()
            flash('Revenue type added successfully.')
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}')
        finally:
            cursor.close()
        
        return redirect(url_for('revenue_dashboard'))

    return render_template('add_revenue.html', form=form)


@app.route('/revenue_dashboard')
def revenue_dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT rt.revenuetypeid, rt.revenue, isc.name 
        FROM revenuetype rt
        JOIN investmentsubcatg isc ON rt.investmentsubcatgid = isc.id
    """)
    revenues = cursor.fetchall()
    cursor.close()
    
    print(revenues)  # Debug: print fetched data
    
    return render_template('revenue_dashboard.html', revenues=revenues)


@app.route('/update_revenue/<int:revenue_id>', methods=['GET', 'POST'])
def update_revenue(revenue_id):
    form = EditRevenueForm()

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT investmentsubcatgid, revenue FROM revenuetype WHERE revenuetypeid = %s", (revenue_id,))
    revenue_data = cursor.fetchone()
    cursor.close()

    if revenue_data:
        form.revenue_id.data = revenue_id
        form.revenue.data = revenue_data[1]  # Assign revenue data

        # Fetch subcategory options from the database and populate the SelectField choices
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name FROM investmentsubcatg")
        subcategories = cursor.fetchall()
        cursor.close()

        form.subcategory.choices = [(subcat[0], subcat[1]) for subcat in subcategories]
        form.subcategory.data = revenue_data[0]  # Assign selected subcategory ID

    if form.validate_on_submit():
        action = request.form['action']

        if action == 'Update':
            subcategory = form.subcategory.data
            revenue = form.revenue.data

            cursor = mysql.connection.cursor()
            try:
                cursor.execute(
                    "UPDATE revenuetype SET investmentsubcatgid=%s, revenue=%s WHERE revenuetypeid=%s",
                    (subcategory, revenue, revenue_id)
                )
                mysql.connection.commit()
                flash('Revenue updated successfully.')
            except MySQLdb.Error as e:
                mysql.connection.rollback()
                flash(f'Error updating revenue: {str(e)}')
            finally:
                cursor.close()

        elif action == 'Clear':
            cursor = mysql.connection.cursor()
            try:
                cursor.execute(
                    "UPDATE revenuetype SET investmentsubcatgid=NULL, revenue=NULL WHERE revenuetypeid=%s",
                    (revenue_id,)
                )
                mysql.connection.commit()
                flash('Revenue cleared successfully.')
            except MySQLdb.Error as e:
                mysql.connection.rollback()
                flash(f'Error clearing revenue: {str(e)}')
            finally:
                cursor.close()

        return redirect(url_for('revenue_dashboard'))

    return render_template('update_revenue.html', form=form)


@app.route('/delete_revenue/<int:revenue_id>', methods=['POST'])
def delete_revenue(revenue_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM revenuetype WHERE revenuetypeid = %s", (revenue_id,))
        mysql.connection.commit()
        flash('Revenue record deleted successfully.')
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f'Error deleting revenue record: {str(e)}')
    finally:
        cursor.close()
    
    return redirect(url_for('revenue_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)