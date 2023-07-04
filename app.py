from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, StringField, PasswordField, validators
from flask_login import LoginManager, current_user, UserMixin, login_user, logout_user, login_required
from models.model import predict_fake_news
import re

app = Flask(__name__, static_url_path='/static')

app.config['SECRET_KEY'] = 'esp2023@'  # Clé secrète pour sécuriser les sessions
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fake_news'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
login_manager = LoginManager(app)   
# Définir une classe User personnalisée en utilisant UserMixin de Flask-Login
class User(UserMixin):
    def __init__(self, user_id, firstname, lastname, password, email, is_admin, is_verificator):
        self.id = user_id
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.email = email
        self.is_admin = is_admin
        self.is_verificator = is_verificator

@login_manager.user_loader
def load_user(user_id):
    # Implémentez cette fonction pour charger et renvoyer l'utilisateur à partir de l'ID d'utilisateur (user_id)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    if user:
        user_obj = User(user['id'], user['firstname'], user['lastname'], user['password'], user['email'],
                        user['is_admin'],user['is_verificator'])
        return user_obj
    else:
        return None


# Classe du formulaire d'inscription
class SignupForm(Form):
    firstname = StringField('Prénom', [validators.DataRequired()])
    lastname = StringField('Nom', [validators.DataRequired()])
    email = StringField('Adresse Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Mot de passe', [
        validators.DataRequired(),
        validators.Length(min=6)
    ])


# Classe du formulaire de connexion
class LoginForm(Form):
    email = StringField('Adresse Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Mot de passe', [validators.DataRequired()])


# Page d'accueil / Inscription
@app.route('/')
def home():
    return render_template('acceuil.html')


@app.route('/static')
def serve_css():
    return app.send_static_file('style.css')
# Page d'utilisateur
@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    username = current_user.firstname + " " + current_user.lastname
    result = None

    if request.method == 'POST':
        link = request.form['link']
        result = predict_fake_news(link)
        return render_template('result.html', username=username, result=result,link=link)

    return render_template('user.html', username=username)


# Page de déconnexion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# Page d'inscription
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        password = form.password.data

        # Vérifier si l'utilisateur existe déjà dans la base de données
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            error = 'Cet utilisateur existe déjà.'
            return render_template('signup.html', form=form, error=error)

        # Créer un nouvel utilisateur et l'ajouter à la base de données
        cur.execute("INSERT INTO users (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)",
                    (firstname, lastname, email, generate_password_hash(password)))
        mysql.connection.commit()
        cur.close()

        # Rediriger vers la page de connexion après l'inscription réussie
        return redirect('/login')

    return render_template('signup.html', form=form)


# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data

        # Vérifier les informations de connexion de l'utilisateur dans la base de données
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            # Les informations d'identification sont correctes, connectez l'utilisateur
            user_obj = User(user['id'], user['firstname'], user['lastname'], user['password'], user['email'],
                            user['is_admin'],user['is_verificator'])
            login_user(user_obj)
            if user_obj.is_admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))
        else:
            # Les informations d'identification sont incorrectes, afficher un message d'erreur
            error = 'Adresse email ou mot de passe incorrect.'
            return render_template('login.html', form=form, error=error)

    return render_template('login.html', form=form)


@app.route('/update_account', methods=['GET', 'POST'])
@login_required
def update_account():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        password = form.password.data

        # Vérifier si un nouveau mot de passe a été saisi
        if password:
            hashed_password = generate_password_hash(password)
        else:
            hashed_password = current_user.password

        # Mettre à jour les informations de l'utilisateur dans la base de données
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET firstname = %s, lastname = %s, email = %s, password = %s WHERE id = %s",
                    (firstname, lastname, email, hashed_password, current_user.id))
        mysql.connection.commit()
        cur.close()

        # Rediriger vers la page de profil de l'utilisateur avec un message de succès
        flash('Les informations du compte ont été mises à jour avec succès', 'success')
        return redirect('/user')

    return render_template('update_account.html', form=form)


# Page d'administration
@app.route('/admin')
@login_required
def admin():
    if current_user.is_admin:
        # Récupérer la liste des utilisateurs depuis la base de données
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.close()

        return render_template('admin/admin.html', users=users)
    else:
        flash('Accès refusé. Vous n\'êtes pas administrateur.', 'error')
        return redirect('/')


# Page de modification d'utilisateur
@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.is_admin:
        # Récupérer les informations de l'utilisateur à partir de l'ID
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Afficher le formulaire de modification avec les informations de l'utilisateur
            form = SignupForm(request.form)
            form.firstname.data = user['firstname']
            form.lastname.data = user['lastname']
            form.email.data = user['email']

            if request.method == 'POST' and form.validate():
                # Mettre à jour les informations de l'utilisateur dans la base de données
                firstname = form.firstname.data
                lastname = form.lastname.data
                email = form.email.data

                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET firstname = %s, lastname = %s, email = %s WHERE id = %s",
                            (firstname, lastname, email, user_id))
                mysql.connection.commit()
                cur.close()

                flash('Utilisateur mis à jour avec succès.', 'success')
                return redirect('/admin')

            return render_template('admin/edit_user.html', form=form, user_id=user_id)
        else:
            flash('Utilisateur non trouvé.', 'error')
            return redirect('/admin')
    else:
        flash('Accès refusé. Vous n\'êtes pas administrateur.', 'error')
        return redirect('/')


# Page de suppression d'utilisateur
@app.route('/admin/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.is_admin:
        # Supprimer l'utilisateur de la base de données
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()

        flash('Utilisateur supprimé avec succès.', 'success')
        return redirect('/admin')
    else:
        flash('Accès refusé. Vous n\'êtes pas administrateur.', 'error')
        return redirect('/')


# Page de création d'utilisateur
@app.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.is_admin:
        form = SignupForm(request.form)

        if request.method == 'POST' and form.validate():
            # Créer un nouvel utilisateur et l'ajouter à la base de données
            firstname = form.firstname.data
            lastname = form.lastname.data
            email = form.email.data
            password = form.password.data

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)",
                        (firstname, lastname, email, generate_password_hash(password)))
            mysql.connection.commit()
            cur.close()

            flash('Nouvel utilisateur créé avec succès.', 'success')
            return redirect('/admin')

        return render_template('admin/create_user.html', form=form)
    else:
        flash('Accès refusé. Vous n\'êtes pas administrateur.', 'error')
        return redirect('/')


# Page de résultats
@app.route('/result', methods=['GET', 'POST'])
@login_required
def result():
    if request.method == 'POST':
        link = request.form['link']
        result = predict_fake_news(link)

        # Stocker le résultat dans la table "information" pour vérification ultérieure
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO information (user_id, link, result) VALUES (%s, %s, %s)",
                    (current_user.id, link, result))
        mysql.connection.commit()
        cur.close()

        return render_template('result.html', result=result)

    return redirect('/user')

# Page de résultats
@app.route('/submit', methods=['POST'])
@login_required
def submit():
    if request.method == 'POST':
        link = request.form['link']
        result = request.form['result']

        # Stocker le résultat dans la table "information" pour vérification ultérieure
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO information (user_id, link, result) VALUES (%s, %s, %s)",
                    (current_user.id, link, result))
        mysql.connection.commit()
        cur.close()

        return render_template('result.html', result=result, link=link)
    return redirect('/user')
#Page du vérificateur de faits
@app.route('/verificator')
@login_required
def verificator():
    if current_user.is_verificator:
        # Récupérer les informations à vérifier depuis la base de données
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM information order by created_at")
        informations = cur.fetchall()
        cur.close()
        users = current_user.email
        return render_template('verificator.html', informations=informations,users=users)
    else:
        flash('Accès refusé. Vous n\'êtes pas vérificateur.', 'error')
        return redirect('/user')

@app.route('/verificator/delete', methods=['POST'])
@login_required
def delete_information():
    if current_user.is_verificator:
        information_id = request.form['information_id']

        # Effectuez les opérations de suppression dans la base de données
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM information WHERE id = %s", (information_id,))
        mysql.connection.commit()
        cur.close()

        flash('Information supprimée avec succès.', 'success')
        return redirect('/verificator')
    else:
        flash('Accès refusé. Vous n\'êtes pas vérificateur.', 'error')
        return redirect('/user')

@app.route('/submit_verificator_result', methods=['POST'])
def submit_verificator_result():
    information_id = request.form.get('information_id')
    additional_test = request.form.get('additional_test')
    
    # Retrieve the information from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM information WHERE id = %s", (information_id,))
    information = cur.fetchone()
    cur.close()
    
    if information:
        # Update the information status
        cur = mysql.connection.cursor()
        cur.execute("UPDATE information SET status = %s WHERE id = %s", (additional_test, information_id))
        mysql.connection.commit()
        cur.close()

        flash('Résultat vérificateur soumis avec succès.', 'success')
        return redirect('/verificator')
    else:
        flash('L\'information n\'a pas été trouvée.', 'error')
        return redirect('/verificator')
    
@app.route('/result_verificator')
@login_required
def result_verificator():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM information WHERE user_id = %s", (current_user.id,))
    informations = cur.fetchall()
    cur.close()

    if informations:
        return render_template('result_verificator.html', informations=informations)
    else:
        flash('L\'information n\'a pas été trouvée.', 'error')
        return redirect('/user')

@app.route('/result_verificator/delete', methods=['POST'])
@login_required
def delete_information_result():
    information_id = request.form['information_id']
    
    # Perform the delete operation in the database
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM information WHERE id = %s", (information_id,))
    mysql.connection.commit()
    cur.close()
    flash('Information supprimée avec succès.', 'success')
    return redirect('/user')
    
if __name__ == '__main__':
    app.run(debug=True)
