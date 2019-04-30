import string, random


def random_string(length=32, charset=None):
    if charset is None:
        charset = string.ascii_letters + string.digits

    return "".join(random.choice(charset) for _ in range(length))


def likelihood_of_collision(length=32, charset=None):
    if charset is None:
        charset = string.ascii_letters + string.digits

    return "%.2g" % len(charset) ** length