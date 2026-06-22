from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_nonexistent_patient_returns_404():
    with patch("app.routers.patient.get_patient_info_from_id", return_value=None):
        response = client.get("/api/patient/NONEXISTENT")
    assert response.status_code == 404
