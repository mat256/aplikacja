import pytest
from datetime import date
from aplikacja.db import get_db


def test_login_required(client, app):
    response = client.get('dashboard/')
    assert response.headers["Location"] == "/auth/login"
    response = client.get('dashboard/graph')
    assert response.headers["Location"] == "/auth/login"
    response = client.get('dashboard/lastweeks')
    assert response.headers["Location"] == "/auth/login"

def test_graph(client, auth, app):
    auth.login()
    assert client.get('dashboard/graph').status_code == 200
    assert client.post('dashboard/graph', data={'date': "1900-01-01"}).status_code ==200

def test_14d_graph(client, auth, app):
    auth.login()
    assert client.get('dashboard/lastweeks').status_code == 302

    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO data(author_id, custom_date, glucose) VALUES(1,?,180);",
                   (str(date.today()) +' 00:00:00',))
        db.execute("INSERT INTO insulin(author_id, custom_date, amount, period) VALUES(1,?,12,180);",
                   (str(date.today())+' 00:00:00',))
        db.commit()
    assert client.get('dashboard/lastweeks').status_code == 200



def test_main_page(client, auth, app):
    auth.login()
    #response = client.get('dashboard/')
    #assert response.data == 200
    assert client.get('dashboard/').status_code == 200
    with app.app_context():
        db = get_db()
        db.execute('UPDATE insulin SET author_id = 2 WHERE id = 1')
        db.commit()
    response = client.get('dashboard/')
    assert b'User needs to upload glucose data.' in response.data
    with app.app_context():
        db = get_db()
        db.execute('UPDATE data SET author_id = 2 WHERE id = 1')
        db.commit()
    response = client.get('dashboard/')
    assert b'User needs to upload glucose data.' in response.data



