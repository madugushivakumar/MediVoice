import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "voice-agent"))

from app.services.appointment_service import AppointmentService

def test_phone_normalization():
    assert AppointmentService.normalize_phone("9876543210") == "9876543210"
    assert AppointmentService.normalize_phone("+91 98765 43210") == "9876543210"
    assert AppointmentService.normalize_phone("09876543210") == "9876543210"
    assert AppointmentService.normalize_phone("919876543210") == "9876543210"

def test_phone_validation():
    # Valid Indian mobile numbers
    assert AppointmentService.validate_phone("9876543210") is True
    assert AppointmentService.validate_phone("8123456789") is True
    assert AppointmentService.validate_phone("7000123456") is True
    assert AppointmentService.validate_phone("6300987654") is True

    # Invalid cases
    assert AppointmentService.validate_phone("1234567890") is False  # Does not start with 6-9
    assert AppointmentService.validate_phone("98765") is False       # Too short
    assert AppointmentService.validate_phone("9876543210123") is False # Too long
    assert AppointmentService.validate_phone("") is False

def test_phone_masking():
    assert AppointmentService.mask_phone("9876543210") == "******3210"
    assert AppointmentService.mask_phone("+919876543210") == "********3210"
    assert AppointmentService.mask_phone("123") == "123"
