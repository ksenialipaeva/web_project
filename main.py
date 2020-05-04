from flask import Flask, render_template, redirect, request, abort
from data import db_session
from data.books import Books
from flask_wtf import FlaskForm
from flask_wtf.html5 import EmailField
from wtforms import StringField, PasswordField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from data.users import User
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/library.sqlite")
    app.run()


@app.route("/")
def index():
    session = db_session.create_session()
    books = session.query(Books).all()
    if current_user.is_authenticated:
        if current_user.id == 1:
            my_books = []
        else:
            my_books = session.query(Books).filter(Books.user_id == current_user.id)
            books = session.query(Books).filter(Books.user_id != current_user.id)
    else:
        my_books = []
    return render_template("index.html", books=books, my_books = my_books)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/books',  methods=['GET', 'POST'])
@login_required
def add_books():
    form = BooksForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        books = Books()
        books.title = form.title.data
        books.author = form.author.data
        books.genre = form.genre.data
        current_user.books.append(books)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    return render_template('book.html', title='Добавление книги', form=form)


@app.route('/books/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_books(id):
    form = BooksForm()
    if request.method == "GET":
        session = db_session.create_session()
        books = session.query(Books).filter(Books.id == id).first()
        if books:
            form.title.data = books.title
            form.author.data = books.author
            form.genre.data = books.genre
            form.user_id.data = books.user_id
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        books = session.query(Books).filter(Books.id == id).first()
        if books:
            books.title = form.title.data
            books.author = form.author.data
            books.genre = form.genre.data
            books.user_id = form.user_id.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('book.html', title='Редактирование книги', form=form)


@app.route('/books_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    session = db_session.create_session()
    books = session.query(Books).filter(Books.id == id, Books.user == current_user).first()
    if books:
        session.delete(books)
        session.commit()
    else:
        abort(404)
    return redirect('/')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    surname = StringField('Фамилия пользователя', validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class BooksForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    author = StringField('Автор')
    genre = StringField('Жанр')
    user_id = IntegerField('ID текущего владельца')
    submit = SubmitField('Применить')


if __name__ == '__main__':
    main()