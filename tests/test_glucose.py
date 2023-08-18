import pytest
from aplikacja.db import get_db

@pytest.mark.parametrize('path', (
    'data/glucose/create',
    'data/glucose/1/update',
    'data/glucose/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE data SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('data/glucose/1/update').status_code == 403
    assert client.post('data/glucose/1/delete').status_code == 403

def test_create(client, auth, app):
    auth.login()
    assert client.get('data/glucose/create').status_code == 200
    client.post('data/glucose/create', data={'glucose': 140, 'activity':'test', 'info': 'test', 'date': "1900-01-01"})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM data').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('data/glucose/1/update').status_code == 200
    client.post('data/glucose/1/update', data={'glucose': 100, 'activity':'updated', 'info': 'updated'})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM data WHERE id = 1').fetchone()
        assert post['activity'] == 'updated'
        assert post['info'] == 'updated'



def test_create_validate(client, auth, app):
    auth.login()
    response = client.post('data/glucose/create', data={'glucose': 't', 'activity':'test', 'info': 'test', 'date': "1900-01-01"})
    assert b'Glucose must be integer number.' in response.data

def test_update_validate(client, auth, app):
    auth.login()
    response = client.post('data/glucose/1/update', data={'glucose': 't', 'activity': '', 'info': 'test', 'date': "1900-01-01"})
    assert b'Glucose must be integer number.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('data/glucose/1/delete')
    assert response.headers["Location"] == "/data/glucose/all"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM data WHERE id = 1').fetchone()
        assert post is None