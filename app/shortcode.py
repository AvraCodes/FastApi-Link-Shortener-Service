import random
import string

ALPHABET = string.ascii_letters + string.digits  # base62


def generate_short_code(length: int = 7) -> str:
    return "".join(random.choices(ALPHABET, k=length))
