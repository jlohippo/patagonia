import pytest
from app import create_app
from models import db, ProductMonitor

@pytest.fixture
def client():
    app = create_app('sqlite:///:memory:')
    app.config['TESTING'] = True

    with app.app_context():
        # Clear database and recreate tables just to be sure
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_index_empty(client):
    rv = client.get('/')
    assert b'No products are being monitored' in rv.data

def test_add_and_delete_product(client):
    # Add product
    rv = client.post('/add', data=dict(
        name='Test Jacket',
        url='https://www.patagonia.com/test-jacket',
        size='M',
        color='Blue',
        target_discount_percent='20.0'
    ), follow_redirects=True)

    assert b'Test Jacket' in rv.data
    assert b'https://www.patagonia.com/test-jacket' in rv.data

    # Check DB
    from app import create_app
    app = create_app('sqlite:///:memory:') # This doesn't share memory context in standard setup easily, let's just use the app context trick below if needed, or stick to route checking.

    # Let's extract the product ID from the HTML or just delete the first one since it's the only one
    html_content = rv.data.decode('utf-8')
    assert 'action="/delete/1"' in html_content

    # Delete product
    rv = client.post('/delete/1', follow_redirects=True)
    assert b'No products are being monitored' in rv.data
