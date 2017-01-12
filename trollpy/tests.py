"""Tests for TrollyPy App."""
import pytest
import transaction
import os
from pyramid import testing
from .models.meta import Base
from .models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    User,
    KillScore
)


@pytest.fixture(scope="function")
def sqlengine(request):
    """Return sql engine."""
    config = testing.setUp(settings={
        'sqlalchemy.url': os.environ["DATABASE_URL"]
    })
    config.include(".models")
    settings = config.get_settings()
    engine = get_engine(settings)
    Base.metadata.create_all(engine)

    def teardown():
        testing.tearDown()
        transaction.abort()
        Base.metadata.drop_all(engine)

    request.addfinalizer(teardown)
    return engine


@pytest.fixture(scope="function")
def new_session(sqlengine, request):
    """Return new session."""
    session_factory = get_session_factory(sqlengine)
    session = get_tm_session(session_factory, transaction.manager)

    def teardown():
        transaction.abort()

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def dummy_request(new_session, method="GET"):
    """Instantiate a fake HTTP Request, complete with a database session."""
    request = testing.DummyRequest()
    request.method = method
    request.dbsession = new_session
    return request


@pytest.fixture
def dummy_post_request(new_session, method="POST"):
    """Instantiate a fake HTTP Request, complete with a database session."""
    request = testing.DummyRequest()
    request.method = method
    request.dbsession = new_session
    return request


@pytest.fixture
def testapp():
    """Create an instance of webtests TestApp for testing routes."""
    from webtest import TestApp
    from trollpy import main

    app = main({}, **{'sqlalchemy.url': os.environ["DATABASE_URL"]})
    testapp = TestApp(app)

    session_factory = app.registry["dbsession_factory"]
    engine = session_factory().bind
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return testapp


@pytest.fixture
def fill_the_db(testapp):
    """Fill the database with some model instances."""
    session_factory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        user = User(username='amos',
                    password='password',
                    first_name='Amos',
                    last_name='Boldor',
                    email='amosboldor@gmail.com')
        kill_score = KillScore(killscore_id='-8',
                               statement='You live because I allowed it.')
        dbsession.add(kill_score)
        dbsession.add(user)

# ======== UNIT TESTS ==========


# def test_registration_view(dummy_post_request):
#     """Test that adding a user adds a new user to the database."""
#     from .views.default import registration_view
#     dummy_post_request.POST["username"] = 'dude'
#     dummy_post_request.POST["password"] = 'password'
#     dummy_post_request.POST["first_name"] = 'dude'
#     dummy_post_request.POST["last_name"] = 'mcklovine'
#     dummy_post_request.POST["email"] = 'asdas@gmas.com'
#     registration_view(dummy_post_request)
#     assert dummy_post_request.dbsession.query(User).filter_by(username='dude').first_name()

# ======== FUNCTIONAL TESTS ===========


def test_home_page_pops_up(testapp):
    """Test that home page get sent correctly."""
    response = testapp.get('/', status=200)
    assert response.status_code == 200


def test_login_leads_to_home(testapp, fill_the_db):
    """Test that after logging in it sends you to the home route."""
    response = testapp.post('/login',
                            params={'username': 'amos',
                                    'password': 'password'}).follow()
    assert response.status_code == 200


def test_login_show_form(testapp):
    """Test that the login route shows form."""
    response = testapp.get('/login', status=200)
    assert response.status_code == 200
    assert response.html.find('form')


def test_logout(testapp):
    """Test that logging out has 200 ok code."""
    testapp.post('/login',
                 params={'username': 'amos',
                         'password': 'password'})
    response = testapp.get('/logout', status=302).follow()
    assert response.status_code == 200
    assert response.html.find_all('a')[0].text == 'log in'


def test_registration_show_form(testapp):
    """Test that the registration route shows form."""
    response = testapp.get('/login', status=200)
    assert response.status_code == 200
    assert response.html.find('form')


def test_profile_route(testapp, fill_the_db):
    """Test that the profile route pops up with correct info."""
    testapp.post('/login',
                 params={'username': 'amos',
                         'password': 'password'}).follow()
    response = testapp.get('/profile/amos', status=200)
    assert 'amosboldor@gmail.com' in response.html.find_all('li')[2].text
    assert 'Amos Boldor' in response.html.find_all('li')[1].text


def test_smack_api_route(testapp, fill_the_db):
    """Test smack_api to return kill_score json."""
    response = testapp.get('/smack_api', status=200)
    assert len(response.json) == 1


def test_new_user(testapp):
    """Test that adding a new user via registration page."""
    user = {
        'username': 'dude',
        'password': 'password',
        'first_name': 'dude',
        'last_name': 'asdasd',
        'email': 'gofuckyour@skdgmsk',

    }
    html = testapp.post('/registration', user, status=302).follow().html
    assert 'gofuckyour@skdgmsk' in html.find_all('li')[2].text
    assert 'dude asdasd' in html.find_all('li')[1].text


def test_add_smack(testapp):
    """Test that add_smack route shows form."""
    response = testapp.get('/add_smack', status=200)
    assert len(response.html.find_all('form')) == 1


def test_add_smack_post(testapp):
    """Test adding smack to db."""
    kill_score = {'killscore_id': -1, 'statement': 'aosidnaosidj'}
    testapp.post('/add_smack', kill_score, status=302)
    assrtion = testapp.get('/smack_api', status=200)
    assert kill_score['statement'] == assrtion.json[0]['statement']


def test_user_board_json(testapp, fill_the_db):
    """Test that get user board gets current chess board."""
    board = testapp.get('/amos/api', status=200).json['board']
    assert board == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
