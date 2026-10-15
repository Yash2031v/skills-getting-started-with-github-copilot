import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def test_activity(monkeypatch: pytest.MonkeyPatch) -> str:
    name = "Test Activity"
    monkeypatch.setitem(
        activities,
        name,
        {
            "description": "An activity for API tests",
            "schedule": "Mondays",
            "max_participants": 10,
            "participants": [],
        },
    )
    return name


def test_get_activities_includes_activity_and_disables_caching(
    client: TestClient, test_activity: str
) -> None:
    # Arrange
    expected_activity = activities[test_activity]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[test_activity] == expected_activity
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(
    client: TestClient, test_activity: str
) -> None:
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.post(
        f"/activities/{test_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {test_activity}"
    }
    assert email in activities[test_activity]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client: TestClient) -> None:
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@example.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(
    client: TestClient, test_activity: str
) -> None:
    # Arrange
    email = "student@example.edu"
    activities[test_activity]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{test_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities[test_activity]["participants"] == [email]


def test_unregister_removes_participant(
    client: TestClient, test_activity: str
) -> None:
    # Arrange
    email = "student@example.edu"
    activities[test_activity]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{test_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {test_activity}"
    }
    assert email not in activities[test_activity]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(
    client: TestClient,
) -> None:
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@example.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_participant(
    client: TestClient, test_activity: str
) -> None:
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.delete(
        f"/activities/{test_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
