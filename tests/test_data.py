import pytest
from aplikacja.db import get_db


def test_login_required(client, app):
    response = client.get('data/files')
    assert response.headers["Location"] == "/auth/login"
    response = client.post('data/1/delete_file')
    assert response.headers["Location"] == "/auth/login"

def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE file SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('data/1/delete_file').status_code == 403

def test_delete(client, auth, app):
    auth.login()
    response = client.post('data/1/delete_file')
    assert response.headers["Location"] == "/data/files"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM file WHERE id = 1').fetchone()
        assert post is None