from app.shortcode import ALPHABET, generate_short_code


def test_short_code_default_length():
    code = generate_short_code()
    assert len(code) == 7


def test_short_code_custom_length():
    for length in (6, 7, 8):
        code = generate_short_code(length=length)
        assert len(code) == length


def test_short_code_charset():
    code = generate_short_code()
    for char in code:
        assert char in ALPHABET
