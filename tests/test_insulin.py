import pytest
import io
from aplikacja.db import get_db

@pytest.mark.parametrize('path', (
    'data/insulin/create',
    'data/insulin/1/update',
    'data/insulin/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE insulin SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('data/insulin/1/update').status_code == 403
    assert client.post('data/insulin/1/delete').status_code == 403

def test_show_all(client, auth, app):
    auth.login()
    assert client.get('data/insulin/all').status_code == 200

def test_create(client, auth, app):
    auth.login()
    assert client.get('data/insulin/create').status_code == 200

    client.post('data/insulin/create', data={'amount': 8, 'period': 120, 'type': 'test', 'date': "1900-01-01"})
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM insulin').fetchone()[0]
        assert count == 2

    file = open('temp_files/valid_insulin_input.xlsx', 'rb')
    data = {
        'file': file
    }
    client.post('data/insulin/create', data=data)
    with app.app_context():
        db = get_db()
        count2 = db.execute('SELECT COUNT(id) FROM insulin').fetchone()[0]
        assert count2 > count


def test_update(client, auth, app):
    auth.login()
    assert client.get('data/insulin/1/update').status_code == 200
    client.post('data/insulin/1/update', data={'amount': 10, 'period':90,'type':''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM insulin WHERE id = 1').fetchone()
        assert post['amount'] == 10
        assert post['period'] == 90



def test_create_validate(client, auth, app):
    auth.login()
    response = client.post('data/insulin/create', data={'amount': 't','period':90,'type':'', 'date': "1900-01-01"})
    assert b'Insulin amount must be float or integer.' in response.data
    file_name = "test.txt"
    data = {
        'file': (io.BytesIO(b"some initial text data"), file_name)
    }
    response = client.post('/data/insulin/create', data=data)
    assert b'Wrong file extension!' in response.data
    file_name = "test.xlsx"
    data = {
        'file': (io.BytesIO(b"some initial text data"), file_name)
    }
    response = client.post('/data/insulin/create', data=data)
    assert b'Invalid file structure.' in response.data

def test_update_validate(client, auth, app):
    auth.login()
    response = client.post('data/insulin/1/update', data={'amount': 't','period':90,'type':''})
    assert b'Insulin amount must be float or integer.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('data/insulin/5/delete')
    assert b'Entry id 5 doesn&#39;t exist.' in response.data
    response = client.post('data/insulin/1/delete')
    assert response.headers["Location"] == "/data/insulin/all"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM insulin WHERE id = 1').fetchone()
        assert post is None