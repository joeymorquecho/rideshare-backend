from db import User
from db import db


def get_user_by_email(email):
    """
    Returns a user object from the database given an email
    """
    return User.query.filter(User.email == email).first()


def get_user_by_update_token(update_token):
    return User.query.filter(User.update_token == update_token).first()


def verify_credentials(email, password):
    optional_user = get_user_by_email(email)
    if optional_user is None:
        return False, None
    return optional_user.verify_password(password), optional_user


def create_user(name, phone_number, email, password):
    optional_user = get_user_by_email(email)
    if optional_user is not None:
        return False, optional_user
    user = User(name = name, phone_number = phone_number, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return True, user


def renew_session(update_token):
    user = get_user_by_update_token(update_token)
    if user is None:
        return None
    user.renew_session()
    db.session.commit()
    return user
