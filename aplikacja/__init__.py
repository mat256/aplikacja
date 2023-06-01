
import os
from flask_uploads import DOCUMENTS, DATA, UploadSet, configure_uploads

from flask import Flask
from flask import render_template

files = UploadSet("files", DOCUMENTS)
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(

        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    app.config["UPLOADED_FILES_DEST"] = "aplikacja/static/temp_files"

    configure_uploads(app, files)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def index():
        return render_template('index.html')

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import data
    app.register_blueprint(data.bp)
    #app.add_url_rule('/', endpoint='index')

    return app