import pytest


class TestRootEndpoint:
    def test_root_redirects_to_static_index(self, client):
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 307
        assert "/static/index.html" in response.headers.get("location", "")


class TestActivitiesEndpoint:
    def test_get_activities_returns_dictionary(self, client):
        response = client.get("/activities")

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        assert len(payload) > 0

    def test_get_activities_has_expected_fields(self, client):
        response = client.get("/activities")
        payload = response.json()

        for activity_name, details in payload.items():
            assert isinstance(activity_name, str)
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupEndpoint:
    def test_signup_success(self, client, sample_signup):
        response = client.post(
            f"/activities/{sample_signup['activity_name']}/signup",
            params={"email": sample_signup["email"]},
        )

        assert response.status_code == 200
        assert sample_signup["email"] in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": "student@mergington.edu"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email_returns_400(self, client, sample_signup):
        first_response = client.post(
            f"/activities/{sample_signup['activity_name']}/signup",
            params={"email": sample_signup["email"]},
        )
        second_response = client.post(
            f"/activities/{sample_signup['activity_name']}/signup",
            params={"email": sample_signup["email"]},
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert "already signed up" in second_response.json()["detail"]

    def test_signup_accepts_email_with_plus_alias(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "student+alias@mergington.edu"},
        )

        assert response.status_code == 200

    @pytest.mark.xfail(reason="Max participants validation is not implemented yet")
    def test_signup_rejects_when_activity_is_full(self, client):
        activity_name = "Chess Club"
        activity_response = client.get("/activities")
        activity = activity_response.json()[activity_name]

        remaining_slots = activity["max_participants"] - len(activity["participants"])

        for index in range(remaining_slots):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"load{index}@mergington.edu"},
            )
            assert response.status_code == 200

        overflow_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"},
        )
        assert overflow_response.status_code == 400


class TestUnregisterEndpoint:
    def test_unregister_success(self, client, sample_signup):
        signup_response = client.post(
            f"/activities/{sample_signup['activity_name']}/signup",
            params={"email": sample_signup["email"]},
        )
        unregister_response = client.delete(
            f"/activities/{sample_signup['activity_name']}/participants",
            params={"email": sample_signup["email"]},
        )

        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert "Unregistered" in unregister_response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        response = client.delete(
            "/activities/NonExistentActivity/participants",
            params={"email": "student@mergington.edu"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_signed_up(self, client):
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "absent@mergington.edu"},
        )

        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]