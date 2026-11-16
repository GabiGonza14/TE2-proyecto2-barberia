from app.domain.rules import generate_booking_code

BOOKING_CODE_ALPHABET = frozenset("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


def test_generate_booking_code() -> None:
    codes = {generate_booking_code() for _ in range(100)}

    assert all(len(code) == 6 for code in codes)
    assert all(set(code) <= BOOKING_CODE_ALPHABET for code in codes)
