import datetime
import hashlib
import os
import bcrypt
import random
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


passenger_rides = db.Table(
    "passenger association",
    db.Column('passenger_id', db.Integer, db.ForeignKey('user.id')),
    db.Column("passenger_ride_id", db.Integer, db.ForeignKey("ride.id")),
)
# your classes here



class Ride(db.Model):
    """
    Ride Model
    """

    __tablename__ = "ride"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    destination = db.Column(db.String, nullable = False)
    time = db.Column(db.String, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver = db.relationship('User', back_populates= 'rides_giving')
    passengers = db.relationship("User", secondary = passenger_rides, back_populates="rides_going")
    payment = db.Column(db.String, nullable=False)
    additional_info = db.Column(db.String, nullable=False)
    seats_open = db.Column(db.Integer, nullable=False)
    departure_location = db.Column(db.String, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False)

    def __init__(self, **kwargs):
        """
        Initializes a Ride object
        """

        self.destination = kwargs.get("destination", "")
        self.time = kwargs.get("time", "")
        self.payment = kwargs.get("payment", "")
        self.driver_id = kwargs.get("driver_id")
        self.seats_open = kwargs.get("seats_open", "")
        self.additional_info = kwargs.get("additional_info", "")
        self.departure_location = kwargs.get("departure_location", "")
        self.is_completed = False

    def serialize(self):
        """
        Serializes a Ride object
        """

        return {
            "id" : self.id,
            "destination" : self.destination,
            "time" : self.time,
            "driver" : self.driver.simple_serialize(),
            "passengers" : [i.simple_serialize() for i in self.passengers],
            "payment" : self.payment,
            "additional_info" : self.additional_info,
            "departure_location" : self.departure_location,
            "seats_open" : self.seats_open,
            "is_completed" : self.is_completed
        }
    

class User(db.Model):
    """
    User Model
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable = False)
    rides_going = db.relationship("Ride", secondary=passenger_rides, back_populates="passengers")
    rides_giving = db.relationship("Ride", backref = "user", cascade = "delete")
    

    # added for authentication
    email = db.Column(db.String, nullable=False, unique=True)
    password_digest = db.Column(db.String, nullable=False)

    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, **kwargs):
        """
        Initialize an User object
        """
        self.name = kwargs.get("name", "")
        self.phone_number = kwargs.get("phone_number", "")

        
        self.email = kwargs.get("email")
        self.password_digest = bcrypt.hashpw(kwargs.get(
            "password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.phone_number = kwargs.get("phone_number", "")
        self.renew_session()

    def _urlsafe_base_64(self):
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    # Checks if session token is valid and hasn't expired
    def verify_session_token(self, session_token):
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        return update_token == self.update_token

    def serialize(self):
        """
        Serialize a User object
        """
        return{
            "id": self.id,
            "name": self.name,
            "phone_number": self.phone_number,
            "rides_going": [r.serialize() for r in self.rides_going],
            "rides_giving" :  [c.serialize() for c in self.rides_giving],
            "email": [self.email],
            "session_token": self.session_token,
            "session_expiration": str(self.session_expiration),
            "update_token": self.update_token
        
        } 

    def simple_serialize(self):
        """
        serialize a user object without the rides fields
        """

        return{
            "id":self.id,
            "name": self.name,
            "phone_number" : self.phone_number
        }
