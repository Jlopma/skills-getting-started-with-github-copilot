"""
Integration tests for FastAPI endpoints using AAA (Arrange-Act-Assert) pattern.

Tests all HTTP endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Integration tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns all available activities.
        
        AAA Pattern:
        - Arrange: TestClient is ready
        - Act: Send GET request to /activities
        - Assert: Verify response contains all 9 activities with correct structure
        """
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert all(
            "description" in activity and
            "schedule" in activity and
            "max_participants" in activity and
            "participants" in activity
            for activity in activities.values()
        )

    def test_get_activities_response_structure(self, client):
        """
        Test that each activity has required fields with correct types.
        
        AAA Pattern:
        - Arrange: Expected structure defined
        - Act: Get activities response
        - Assert: Validate each activity matches schema
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert set(activity_data.keys()) == required_fields
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Integration tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """
        Test successful signup for an activity.
        
        AAA Pattern:
        - Arrange: Valid activity name and email
        - Act: POST signup request
        - Assert: Verify response and participant is added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_email_returns_400(self, client):
        """
        Test that signup with duplicate email raises 400 error.
        
        AAA Pattern:
        - Arrange: Email already registered in Chess Club
        - Act: Attempt to signup same email again
        - Assert: Verify 400 error and participant count unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        participants_before = client.get("/activities").json()[activity_name]["participants"].copy()
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        
        # Verify no participants were added
        participants_after = client.get("/activities").json()[activity_name]["participants"]
        assert len(participants_before) == len(participants_after)

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Test that signup for nonexistent activity raises 404 error.
        
        AAA Pattern:
        - Arrange: Nonexistent activity name
        - Act: Attempt signup for invalid activity
        - Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_emails(self, client):
        """
        Test that multiple different students can signup for same activity.
        
        AAA Pattern:
        - Arrange: Two unique emails not yet signed up
        - Act: Signup first email, then second
        - Assert: Both emails present in participants list
        """
        # Arrange
        activity_name = "Tennis Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities = client.get("/activities").json()
        participants = activities[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterFromActivity:
    """Integration tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """
        Test successful unregister from an activity.
        
        AAA Pattern:
        - Arrange: Email currently registered in activity
        - Act: DELETE unregister request
        - Assert: Verify response and participant is removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_not_registered_returns_400(self, client):
        """
        Test that unregister for non-registered email raises 400 error.
        
        AAA Pattern:
        - Arrange: Email not registered in activity
        - Act: Attempt to unregister email that's not signed up
        - Assert: Verify 400 error and no participants changed
        """
        # Arrange
        activity_name = "Music Band"
        email = "notregistered@mergington.edu"
        participants_before = client.get("/activities").json()[activity_name]["participants"].copy()
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        
        # Verify no participants were removed
        participants_after = client.get("/activities").json()[activity_name]["participants"]
        assert len(participants_before) == len(participants_after)

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Test that unregister for nonexistent activity raises 404 error.
        
        AAA Pattern:
        - Arrange: Nonexistent activity name
        - Act: Attempt unregister for invalid activity
        - Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client):
        """
        Test that student can unregister and then signup again.
        
        AAA Pattern:
        - Arrange: Student is registered
        - Act: Unregister, verify not in list, signup again
        - Assert: Student is back in participants list
        """
        # Arrange
        activity_name = "Art Studio"
        email = "grace@mergington.edu"  # Already registered
        
        # Act
        # First, unregister
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        activities_after_unregister = client.get("/activities").json()
        
        # Then signup again
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_after_signup = client.get("/activities").json()
        
        # Assert
        assert response_unregister.status_code == 200
        assert email not in activities_after_unregister[activity_name]["participants"]
        
        assert response_signup.status_code == 200
        assert email in activities_after_signup[activity_name]["participants"]
