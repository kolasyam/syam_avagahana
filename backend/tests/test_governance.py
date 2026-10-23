"""
Unit Tests for Governed Workflow and State Transitions
"""

import pytest
from app.api.v1.recommendations import ALLOWED_TRANSITIONS, ROLE_PERMISSIONS

def test_state_machine_valid_transitions():
    assert ALLOWED_TRANSITIONS["DRAFT"]["SUBMIT"] == "SUBMITTED"
    assert ALLOWED_TRANSITIONS["SUBMITTED"]["START_REVIEW"] == "IN_REVIEW"
    assert ALLOWED_TRANSITIONS["IN_REVIEW"]["APPROVE"] == "APPROVED"
    assert ALLOWED_TRANSITIONS["IN_REVIEW"]["REJECT"] == "REJECTED"

def test_role_authorization_rules():
    # Only directors/commissioners/ministers can approve
    assert "Director of Civil Supplies" in ROLE_PERMISSIONS["APPROVE"]
    assert "Analyst" not in ROLE_PERMISSIONS["APPROVE"]
    
    # Analysts can submit
    assert "Analyst" in ROLE_PERMISSIONS["SUBMIT"]
