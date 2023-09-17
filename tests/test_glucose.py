import pytest
import io
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

def test_show_all(client, auth, app):
    response = client.get('data/glucose/all')
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    assert client.get('data/glucose/all').status_code == 200

def test_create(client, auth, app):
    auth.login()
    assert client.get('data/glucose/create').status_code == 200

    client.post('data/glucose/create', data={'glucose': 140, 'activity':'test', 'info': 'test', 'date': "1900-01-01"})
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM data').fetchone()[0]
        assert count == 2

    file = open('temp_files/valid_glucose_input.xlsx', 'rb')
    data = {
        'file': file
    }
    client.post('data/glucose/create', data=data)
    with app.app_context():
        db = get_db()
        count2 = db.execute('SELECT COUNT(id) FROM data').fetchone()[0]
        assert count2 > count
        single = db.execute('SELECT id, file_id,from_file FROM data WHERE custom_date ="2022-10-23 00:04:00"').fetchone()
        assert single['from_file']==1
        #print(single['file_id'])
        file = db.execute('SELECT * FROM file WHERE id = ?',(single['file_id'],)).fetchone()
        assert file['name'] == 'temp_files/valid_glucose_input.xlsx'


def test_update(client, auth, app):
    auth.login()
    assert client.get('data/glucose/1/update').status_code == 200
    client.post('data/glucose/1/update', data={'glucose': 100, 'activity':'updated', 'info': 'updated'})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM data WHERE id = 1').fetchone()
        assert post['glucose'] == 100
        assert post['activity'] == 'updated'
        assert post['info'] == 'updated'



def test_create_validate(client, auth, app):
    auth.login()
    response = client.post('data/glucose/create', data={'glucose': 't', 'activity':'test', 'info': 'test', 'date': "1900-01-01"})
    assert b'Glucose must be integer number.' in response.data

    file_name = "test.txt"
    data = {
        'file': (io.BytesIO(b"some initial text data"), file_name)
    }
    response = client.post('/data/glucose/create', data=data)
    assert b'Wrong file extension!' in response.data

    file_name = "test.xlsx"
    data = {
        'file': (io.BytesIO(b"some initial text data"), file_name)
    }
    response = client.post('/data/glucose/create', data=data)
    assert b'Invalid file structure.' in response.data

def test_update_validate(client, auth, app):
    auth.login()
    response = client.post('data/glucose/1/update', data={'glucose': 't', 'activity': '', 'info': 'test', 'date': "1900-01-01"})
    assert b'Glucose must be integer number.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('data/glucose/12/delete')
    assert b'Entry id 12 doesn&#39;t exist.' in response.data
    response = client.post('data/glucose/1/delete')
    assert response.headers["Location"] == "/data/glucose/all"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM data WHERE id = 1').fetchone()
        assert post is None