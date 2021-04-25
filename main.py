from flask import Flask, session, render_template, request, redirect, url_for, abort, jsonify, send_from_directory
from flask_babel import Babel
import db
import os
from werkzeug.utils import secure_filename
from sqlalchemy.orm.exc import NoResultFound
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

try:
    import data.config as config
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['SITE_URL'] = config.SITE_URL
    app.secret_key = config.SECRET_KEY
    try:
        app.config["DATABASE"] = config.DATABASE
    except AttributeError:
        pass
    app.config['LANGUAGES'] = {
        'en': 'English',
        'de': 'Deutsch',
    }
except ModuleNotFoundError:
    data_path = os.path.join(os.path.abspath(os.path.curdir), "data/")
    if not os.path.exists(os.path.join(data_path, "img/")):
        os.mkdir(os.path.join(data_path, "img/"))
    with open(data_path + "config.py", "w") as f:
        f.write("UPLOAD_FOLDER = '" + os.path.join(data_path, "img/") + "'\n")
        f.write("SITE_URL = 'change.me.in.config.py'\n")
        f.write("SECRET_KEY = " + str(os.urandom(20)) + "\n")
    db.get_session()

babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())


def check_login(session):
    if "login" in session and session["login"]:
        return True
    return False


def is_admin(session):
    if check_login(session):
        db_session = db.get_session()
        user = db_session.query(db.Users).filter_by(username=session["user"]).one()
        return user.admin
    return False


@app.route('/', methods=["get", "post"])
def index():
    db_session = db.get_session()
    admins = db_session.query(db.Users).filter_by(admin=True).all()
    if not admins:  # Check if no admin exists
        # If there is no admin we need to do an initial setup now, and create one
        if request.method == "GET":
            return render_template("initial_setup.html")
        else:
            try:
                username = request.form['setup_username']
                password1 = request.form['setup_password1']
                password2 = request.form['setup_password2']
            except KeyError:
                abort(400)
                raise
            # Create the initial admin
            if password1 != password2:
                return # TODO error out
            pwhash = pbkdf2_sha256.encrypt(password1, rounds=200000, salt_size=16)
            admin_obj = db.Users(username=username, password=pwhash, admin=True)
            db_session.add(admin_obj)
            db_session.commit()
            return redirect(url_for('.index'))
    else:
        if request.method == "GET":
            wrongpw = False
            if request.args.get('pw') == "1":
                wrongpw = True
            return render_template("index.html", wrongpw=wrongpw, logged_in=False)  # TODO set logged in
            # TODO also have a switch for: Should we show the registration form?
        else:
            # Check password
            try:
                username = request.form['login_username']
                password = request.form['login_password']
            except KeyError:
                if False:  # TODO check if registration is not allowed
                    abort(400)
                    raise
                try:
                    username = request.form['register_username']
                    password1 = request.form['register_password1']
                    password2 = request.form['register_password2']
                    # TODO registration logic goes in here
                except KeyError:
                    abort(400)
                    raise

            # Continue with login logic
            user = db_session.query(db.Users).filter_by(username=username).one()

            if pbkdf2_sha256.verify(password, user.password):
                session["login"] = True
                session["user"] = user.username
                return redirect(url_for('.manage'))
            else:
                return redirect(url_for('.index') + '?pw=1')


@app.route('/manage/logout/')
def logout():
    if not check_login(session):
        return redirect(url_for('.index'))
    session.pop("login", None)
    session.pop("user", None)
    return redirect(url_for('.index'))


@app.route('/manage/admin/')  # Admin site (should be a very dense list of all users, and sites)
def admin():
    if not is_admin(session):
        abort(403)
    db_session = db.get_session()
    users = db_session.query(db.Users).all()
    sites = db_session.query(db.Sites).all()
    return render_template("admin.html", users=users, sites=sites)


@app.route('/manage/admin/user/create/', methods=["get", "post"])  # Create a user
def admin_user_create():
    if not is_admin(session):
        abort(403)

    if request.method == "GET":
        return render_template("admin_create_user.html")
    else:
        pass  # TODO do the creating


@app.route('/manage/admin/user/<string:user>/', methods=["get", "post"])  # User-details (e.g.: What sites did they create)
def admin_user_detail():
    if not is_admin(session):
        abort(403)
    # TODO


@app.route('/manage/admin/user/<string:user>/delete/', methods=["post"])
def admin_user_delete():
    if not is_admin(session):
        abort(403)
    # TODO


@app.route('/manage/admin/site/<string:name>/', methods=["get", "post"])  # Details about site
def admin_site_detail():
    if not is_admin(session):
        abort(403)
    # TODO


@app.route('/manage/admin/site/<string:name>/delete/', methods=["post"])
def admin_site_delete():
    if not is_admin(session):
        abort(403)
    # TODO


@app.route('/manage/admin/config/', methods=["get", "post"])  # Config switches
def admin_config():
    if not is_admin(session):
        abort(403)
    # TODO


@app.route('/manage/')  # Manage links site (for users and admins)
def manage():
    if not check_login(session):
        return redirect(url_for('.login'))
    # TODO


@app.route('/manage/create/', methods=["get", "post"])  # Create new site
def manage_create_site():
    if not check_login(session):
        return redirect(url_for('.login'))

    if request.method == "GET":
        return render_template("create_site.html")
    else:
        try:
            pass
            # TODO take request.form['...'] data here
        except KeyError:
            abort(400)

        db_session = db.get_session()
        obj = db.Sites(
            # TODO ...
        )
        db_session.add(obj)
        db_session.commit()

        # TODO add an uploaded icon here

        """
        try:
            if request.form['img_list'] != "":
                images = request.form['img_list'].split(";")
                for image in images:
                    pic_obj = db.Pictures(shoot=obj, filename=image)
                    db_session.add(pic_obj)
                db_session.commit()
        except KeyError:
            pass
        """

        return redirect(url_for('.manage_site', name=obj.name))


@app.route('/manage/<string:name>/', methods=["get", "post"])  # Manage site
def manage_site(name):
    if not check_login(session):
        abort(403)

    db_session = db.get_session()
    try:
        obj = db_session.query(db.Sites).filter_by(name=name).one()
    except NoResultFound:
        abort(404)

    # TODO check ownership

    if request.method == "GET":
        return render_template("manage_site.html", site=obj)
    elif request.method == "POST":
        try:
            # Route 1: Updating Data
            """
            description = request.form['description']
            limit = request.form['limit']
            obj.description = description
            obj.max_images = limit"""
            db_session.commit()
            return redirect(url_for(".manage_site", name=obj.name))
        except KeyError:
            # Route 2: Uploading an icon
            try:
                """images = request.form['img_list'].split(";")
                for image in images:
                    pic_obj = db.Pictures(shoot=obj, filename=image)
                    db_session.add(pic_obj)"""
                db_session.commit()

                return jsonify(data="success")
            except KeyError:
                abort(400)


@app.route('/manage/<string:name>/upload/', methods=["post"])  # Upload an image
def manage_upload(name):
    if not check_login(session):
        abort(403)

    db_session = db.get_session()
    try:
        obj = db_session.query(db.Sites).filter_by(name=name).one()
    except NoResultFound:
        abort(404)

    file = request.files["files[]"]
    filename = file.filename.replace(" ", "_")
    if filename == '':  # when no file is selected filename is empty, without data
        return jsonify(error="No file selected")
    if file:
        sec_filename = secure_filename(filename)
        # Check if the file already exists and rename it silently
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], sec_filename)):
            sec_filename = os.path.splitext(sec_filename)[0] + "_conflict" + os.path.splitext(sec_filename)[1]

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], sec_filename))

        obj.icon = sec_filename
        db_session.commit()

        return jsonify(files=[{
            "name": sec_filename,
            "url": "/img/" + sec_filename,
        }, ])


@app.route('/manage/<string:name>/delete/', methods=["post"])  # Delete site
def manage_delete(name):
    if not check_login(session):
        abort(403)

    db_session = db.get_session()
    try:
        obj = db_session.query(db.Sites).filter_by(name=name).one()
    except NoResultFound:
        abort(404)

    # TODO check ownership (not just here)

    # TODO delete the icon file
    """
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], obj.icon)
    try:
        os.unlink(picture_path)
    except FileNotFoundError:
        pass
    """
    db_session.delete(obj)
    db_session.commit()
    return redirect(url_for(".manage"))


@app.route('/manage/pwchange/', methods=["get", "post"])
def manage_pwchange():
    if not check_login(session):
        abort(403)
    
    if request.method == "GET":
        if request.args.get('wrong') == "1":
            wrongpw = True
        else:
            wrongpw = False

        if request.args.get('success') == "1":
            changed = True
        else:
            changed = False

        return render_template("pwchange.html", wrongpw=wrongpw, changed=changed)
    elif request.method == "POST":
        try:
            password = request.form['password']
            password2 = request.form['password2']
        except KeyError:
            abort(400)
            raise

        if password != password2:
            return redirect(url_for(".manage_pwchange") + "?wrong=1")
        
        pwhash = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)

        db_session = db.get_session()
        user = db_session.query(db.Users).filter_by(username=session["user"].username).one()
        user.password = pwhash
        db_session.commit()
        
        return redirect(url_for(".manage_pwchange") + "?success=1")


@app.route('/<string:name>/')  # Actual site
def site(name):
    db_session = db.get_session()
    try:
        obj = db_session.query(db.Sites).filter_by(name=name).one()
    except NoResultFound:
        abort(404)

    return render_template("link-page.html", ...)  # vars go there TODO)


@app.route('/img/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
