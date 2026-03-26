"""
Unit tests for FastAPI app business logic using AAA (Arrange-Act-Assert) pattern.

Tests business logic validation and error handling at the unit level:
- Activity lookup and validation
- Participant management
- Error conditions and messages
"""

import pytest
from fastapi import HTTPException


class TestActivityValidation:
    """Unit tests for activity lookup and validation logic."""

    def test_activity_exists_in_app_state(self, client):
        """
        Test that all expected activities exist in app state.
        
        AAA Pattern:
        - Arrange: List of expected activities
        - Act: Fetch all activities from app
        - Assert: Verify each expected activity is present
        """
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Basketball Club",
            "Tennis Club",
            "Art Studio",
            "Music Band",
            "Debate Team",
            "Science Club",
            "Gym Class"
        ]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity in expected_activities:
            assert activity in activities, f"{activity} not found in activities"

    def test_activity_has_valid_participant_count(self, client):
        """
        Test that participant count doesn't exceed max_participants.
        
        AAA Pattern:
        - Arrange: Get current state of activities
        - Act: Fetch all activities
        - Assert: Verify participants <= max_participants for each
        """
        # Arrange
        # (no setup needed)
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            participants = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert participants <= max_participants, \
                f"{activity_name}: {participants} participants exceed max {max_participants}"

    def test_activity_participant_list_is_list_of_strings(self, client):
        """
        Test that participants field is a list of email strings.
        
        AAA Pattern:
        - Arrange: Expected data types
        - Act: Fetch activities
        - Assert: Verify participants list structure
        """
        # Arrange
        # (no setup needed)
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            assert isinstance(participants, list), \
                f"{activity_name} participants is not a list"
            for participant in participants:
                assert isinstance(participant, str), \
                    f"{activity_name} contains non-string participant: {participant}"
                assert "@" in participant, \
                    f"{activity_name} participant '{participant}' is not an email"


class TestSignupValidation:
    """Unit tests for signup business logic validation."""

    def test_signup_adds_participant_to_correct_activity(self, client):
        """
        Test that signup adds participant to the correct activity only.
        
        AAA Pattern:
        - Arrange: Get activities before signup
        - Act: Signup for one activity
        - Assert: Participant added to that activity only, others unchanged
        """
        # Arrange
        target_activity = "Basketball Club"
        other_activities = ["Chess Club", "Tennis Club"]
        email = "newstudent@mergington.edu"
        
        before = client.get("/activities").json()
        before_counts = {
            name: len(data["participants"]) 
            for name, data in before.items()
        }
        
        # Act
        client.post(f"/activities/{target_activity}/signup", params={"email": email})
        
        # Assert
        after = client.get("/activities").json()
        
        # Target activity should have one more participant
        assert len(after[target_activity]["participants"]) == before_counts[target_activity] + 1
        
        # Other activities should be unchanged
        for activity in other_activities:
            assert len(after[activity]["participants"]) == before_counts[activity]

    def test_signup_email_format_preserved(self, client):
        """
        Test that signup preserves the email format passed in.
        
        AAA Pattern:
        - Arrange: Specific email format with uppercase
        - Act: Signup with that email
        - Assert: Email stored exactly as provided
        """
        # Arrange
        activity_name = "Science Club"
        email = "TestStudent@Mergington.edu"  # Mixed case
        
        # Act
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_duplicate_signup_detected_case_sensitive(self, client):
        """
        Test that duplicate detection is case-sensitive for emails.
        
        AAA Pattern:
        - Arrange: Signup with lowercase email
        - Act: Try to signup with different case
        - Assert: Success (emails are treated as case-sensitive)
        """
        # Arrange
        activity_name = "Debate Team"
        email_lower = "newemail@mergington.edu"
        email_upper = "NewEmail@mergington.edu"
        
        # Act
        response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email_lower})
        response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email_upper})
        
        # Assert - both should succeed (case-sensitive)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities = client.get("/activities").json()
        assert email_lower in activities[activity_name]["participants"]
        assert email_upper in activities[activity_name]["participants"]


class TestUnregisterValidation:
    """Unit tests for unregister business logic validation."""

    def test_unregister_removes_from_correct_activity(self, client):
        """
        Test that unregister removes participant from correct activity only.
        
        AAA Pattern:
        - Arrange: Get current state
        - Act: Unregister from one activity
        - Assert: Participant removed from that activity only
        """
        # Arrange
        source_activity = "Chess Club"
        target_activity = "Programming Class"
        email = "michael@mergington.edu"  # Currently in Chess Club
        
        before = client.get("/activities").json()
        before_source_count = len(before[source_activity]["participants"])
        before_target_count = len(before[target_activity]["participants"])
        
        # Act
        client.delete(f"/activities/{source_activity}/unregister", params={"email": email})
        
        # Assert
        after = client.get("/activities").json()
        
        # Source activity should have one fewer participant
        assert len(after[source_activity]["participants"]) == before_source_count - 1
        
        # Target activity should be unchanged
        assert len(after[target_activity]["participants"]) == before_target_count

    def test_unregister_participant_fully_removed(self, client):
        """
        Test that unregister completely removes participant from list.
        
        AAA Pattern:
        - Arrange: Participant is registered
        - Act: Unregister participant
        - Assert: Participant not in list and count decreased
        """
        # Arrange
        activity_name = "Art Studio"
        email = "lucas@mergington.edu"  # Currently registered
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Assert
        activities = client.get("/activities").json()
        participants = activities[activity_name]["participants"]
        
        # Email should not be in the list
        assert email not in participants
        
        # Should appear exactly zero times (not just once removed)
        count = participants.count(email)
        assert count == 0


class TestEndpointErrorMessages:
    """Unit tests for error message clarity and correctness."""

    def test_activity_not_found_message_clear(self, client):
        """
        Test that 404 error message is clear and specific.
        
        AAA Pattern:
        - Arrange: Nonexistent activity name
        - Act: Attempt operation on invalid activity
        - Assert: Error message contains 'Activity not found'
        """
        # Arrange
        fake_activity = "Fake Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_already_signed_up_message_clear(self, client):
        """
        Test that 400 error message for duplicate signup is clear.
        
        AAA Pattern:
        - Arrange: Already registered email
        - Act: Try to signup again
        - Assert: Error message mentions 'already signed up'
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_not_registered_message_clear(self, client):
        """
        Test that 400 error message for unregister non-member is clear.
        
        AAA Pattern:
        - Arrange: Email not registered in activity
        - Act: Try to unregister
        - Assert: Error message mentions 'not registered'
        """
        # Arrange
        activity_name = "Music Band"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_success_message_includes_email_and_activity(self, client):
        """
        Test that success messages include both email and activity name.
        
        AAA Pattern:
        - Arrange: Valid signup parameters
        - Act: Signup for activity
        - Assert: Success message includes both email and activity
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        message = response.json()["message"]
        assert email in message
        assert activity_name in message
