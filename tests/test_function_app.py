import sys
import os
import pytest
import json
from unittest.mock import MagicMock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock azure.functions module
class MockHttpRequest:
    def __init__(self, method, body=None, url="/", route_params=None):
        self.method = method
        self._body = body if body else b""
        self.url = url
        self.route_params = route_params if route_params else {}

    def get_json(self):
        return json.loads(self._body.decode('utf-8')) if self._body else None


class MockHttpResponse:
    def __init__(self, body=None, status_code=200, headers=None, mimetype=None):
        self._body = body
        self.status_code = status_code
        self.headers = headers if headers else {}
        self.mimetype = mimetype

    def get_body(self):
        return self._body


# Create mock azure.functions module
class MockFunctionApp:
    def __init__(self, http_auth_level=None):
        pass

    def route(self, route=None, methods=None):
        def decorator(f):
            def wrapped(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapped
        return decorator


mock_func = MagicMock()
mock_func.HttpRequest = MockHttpRequest
mock_func.HttpResponse = MockHttpResponse
mock_func.AuthLevel = MagicMock()
mock_func.AuthLevel.ANONYMOUS = 'anonymous'
mock_func.FunctionApp = MockFunctionApp

# Apply the mock before importing the app
with patch.dict('sys.modules', {'azure.functions': mock_func}):
    import function_app
    from models import Film, Person, Planet, Species, Vehicle, Starship


# Mock database session
@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session


# Mock database objects
@pytest.fixture
def mock_film():
    return Film(
        id=1,
        title="A New Hope",
        episode_id=4,
        director="George Lucas",
        producer="Gary Kurtz, Rick McCallum",
        release_date="1977-05-25"
    )


@pytest.fixture
def mock_person():
    return Person(
        id=1,
        name="Luke Skywalker",
        height="172",
        mass="77",
        hair_color="blond",
        birth_year="19BBY",
        gender="male"
    )


# Test GET all endpoints
@pytest.mark.parametrize("entity,route", [
    (Film, "films"),
    (Person, "people"),
    (Planet, "planets"),
    (Species, "species"),
    (Vehicle, "vehicles"),
    (Starship, "starships")
])
def test_get_all_success(mock_db_session, entity, route):
    # Arrange
    mock_items = [entity(id=1), entity(id=2)]
    mock_db_session.query.return_value.all.return_value = mock_items
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='GET',
            url=f'/api/{route}',
            route_params={'route': route}
        )
        response = function_app.get_all(req)
        
        # Assert
        assert response.status_code == 200
        assert isinstance(json.loads(response.get_body()), list)
        mock_db_session.query.assert_called_once_with(entity)


@pytest.mark.parametrize("entity,route", [
    (Film, "films"),
    (Person, "people"),
    (Planet, "planets"),
    (Species, "species"),
    (Vehicle, "vehicles"),
    (Starship, "starships")
])
def test_get_all_error(mock_db_session, entity, route):
    # Arrange
    mock_db_session.query.side_effect = Exception("Database error")
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='GET',
            url=f'/api/{route}',
            route_params={'route': route}
        )
        response = function_app.get_all(req)
        
        # Assert
        assert response.status_code == 500
        assert "error" in json.loads(response.get_body())


# Test GET by ID endpoints
@pytest.mark.parametrize("entity,route,mock_obj", [
    (Film, "films", "mock_film"),
    (Person, "people", "mock_person")
])
def test_get_by_id_success(mock_db_session, entity, route, mock_obj, request):
    # Arrange
    mock_item = request.getfixturevalue(mock_obj)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_item
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='GET',
            url=f'/api/{route}/1',
            route_params={'route': route, 'id': '1'}
        )
        response = function_app.get_by_id(req)
        
        # Assert
        assert response.status_code == 200
        response_body = json.loads(response.get_body())
        assert response_body['id'] == 1


def test_get_by_id_not_found(mock_db_session):
    # Arrange
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='GET',
            url='/api/films/999',
            route_params={'route': 'films', 'id': '999'}
        )
        response = function_app.get_by_id(req)
        
        # Assert
        assert response.status_code == 404
        assert json.loads(response.get_body())['error'] == "Not found"


# Test POST endpoints
@pytest.mark.parametrize("entity,route,test_data", [
    (Film, "films", {"title": "Test Film", "episode_id": 1}),
    (Person, "people", {"name": "Test Person", "birth_year": "20BBY"})
])
def test_create_success(mock_db_session, entity, route, test_data):
    # Arrange
    mock_db_session.add = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = MagicMock()
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='POST',
            body=json.dumps(test_data).encode(),
            url=f'/api/{route}',
            route_params={'route': route}
        )
        response = function_app.create(req)
        
        # Assert
        assert response.status_code == 201
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


# Test PUT endpoints
@pytest.mark.parametrize("entity,route,test_data", [
    (Film, "films", {"title": "Updated Film"}),
    (Person, "people", {"name": "Updated Person"})
])
def test_update_success(mock_db_session, entity, route, test_data):
    # Arrange
    mock_item = entity(id=1)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_item
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='PUT',
            body=json.dumps(test_data).encode(),
            url=f'/api/{route}/1',
            route_params={'route': route, 'id': '1'}
        )
        response = function_app.update(req)
        
        # Assert
        assert response.status_code == 200
        mock_db_session.commit.assert_called_once()


def test_update_not_found(mock_db_session):
    # Arrange
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='PUT',
            body=json.dumps({"title": "Updated"}).encode(),
            url='/api/films/999',
            route_params={'route': 'films', 'id': '999'}
        )
        response = function_app.update(req)
        
        # Assert
        assert response.status_code == 404


# Test DELETE endpoints
@pytest.mark.parametrize("entity,route", [
    (Film, "films"),
    (Person, "people"),
    (Planet, "planets"),
    (Species, "species"),
    (Vehicle, "vehicles"),
    (Starship, "starships")
])
def test_delete_success(mock_db_session, entity, route):
    # Arrange
    mock_item = entity(id=1)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_item
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='DELETE',
            url=f'/api/{route}/1',
            route_params={'route': route, 'id': '1'}
        )
        response = function_app.delete(req)
        
        # Assert
        assert response.status_code == 204
        mock_db_session.delete.assert_called_once_with(mock_item)
        mock_db_session.commit.assert_called_once()


def test_delete_not_found(mock_db_session):
    # Arrange
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    with patch('database.get_db', return_value=iter([mock_db_session])):
        # Act
        req = MockHttpRequest(
            method='DELETE',
            url='/api/films/999',
            route_params={'route': 'films', 'id': '999'}
        )
        response = function_app.delete(req)
        
        # Assert
        assert response.status_code == 404
