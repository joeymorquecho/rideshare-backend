import json
import time
from db import db
from flask import Flask, request
from db import Ride
from db import User
import os

app = Flask(__name__)
db_filename = "rideshare.db"

import datetime
import users_dao

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code


def failure_response(message, code=404):
    return json.dumps({"error": message}), code


# your routes here

@app.route("/")
def greet_user():
    return os.environ["NETID"] + " was here!" 

#Ride routes

@app.route("/api/rides/")
def get_rides():
    """
    Endpoint for getting all rides
    """
    rides = [ride.serialize() for ride in Ride.query.all()]
    return success_response({"rides" : rides})

@app.route("/api/rides/<int:driver_id>/", methods=["POST"])
def create_ride(driver_id):
    """
    Endpoint for creating a new ride
    """
    driver_user = User.query.filter_by(id = driver_id).first()
    if driver_user is None:
        return failure_response("Driver not found!")

    body = json.loads(request.data)
    if body.get("destination") is None or body.get("time") is None or body.get("payment") is None \
        or body.get("seats_open") is None or body.get("departure_location") is None:
        return failure_response("Arguments not given.", 400)
    if body.get("additional_info") is None:
        info = ""
    else:
        info = body.get("additional_info")

    new_ride = Ride(
        destination = body.get("destination"),
        time = body.get("time"),
        driver = driver_user,
        driver_id = driver_id,
        payment = body.get("payment"),
        seats_open = body.get("seats_open"),
        departure_location = body.get("departure_location"),
        additional_info = info
    )

    db.session.add(new_ride)
    db.session.commit()
    return success_response(new_ride.serialize(), 201)

@app.route("/api/rides/<int:ride_id>/")
def get_ride(ride_id):
    """
    Endpoint for getting a ride by id
    """
    ride = Ride.query.filter_by(id = ride_id).first()
    if ride is None:
        return failure_response("Ride not found!")
    return success_response(ride.serialize())

@app.route("/api/rides/<string:ride_destination>/")
def get_rides_by_destination(ride_destination):
    """
    Endpoint for getting a ride by destination
    """
    rides = []
    for ride in Ride.query.all():
        if ride.destination == ride_destination:
            rides.append(ride.serialize())
    if len(rides) < 1:
        return failure_response("No rides match the location!")
    return success_response({"rides" : rides})


@app.route("/api/rides/<int:ride_id>/", methods=["DELETE"])
def delete_ride(ride_id):
    """
    Endpoint for deleting a ride by id
    """
    ride = Ride.query.filter_by(id = ride_id).first()
    if ride is None:
        return failure_response("Ride not found!")
    curr_ride = ride.serialize().copy()
    db.session.delete(ride)
    db.session.commit()
    return success_response(curr_ride)

@app.route("/api/rides/complete/<int:ride_id>/", methods=["POST"])
def complete_ride(ride_id):
    """
    Endpoint for change the completion state of the ride to True
    """
    ride = Ride.query.filter_by(id = ride_id).first()
    if ride is None:
        return failure_response("Ride not found!")
    ride.is_completed = True
    db.session.commit()
    return success_response(ride.serialize())

@app.route("/api/users/complete/<int:user_id>/", methods=["GET"])
def get_completed_rides(user_id):
    """
    Endpoint for getting all the rides a user has given in the past
    """
    user = User.query.filter_by(id = user_id).first()
    rides = user.rides_giving
    completed_rides = []
    for ride in rides:
        if ride.is_completed == True:
            completed_rides.append(ride.serialize())

    return success_response({"completed rides" : completed_rides})

#User routes

@app.route("/api/users/", methods=["POST"])
def create_user():
    """
    Endpoint for creating an user
    """
    body = json.loads(request.data)
    if body.get("name") is None or body.get("phone_number") is None :
        return failure_response("Arguments not given.", 400)
    
    if body.get("email") is None or body.get("password") is None:
        return failure_response("Invalid email or password")
    created, user = users_dao.create_user(body.get("name"), body.get("phone_number"), body.get("email"), body.get("password"))

    if not created:
        return failure_response("User already exists.")
    
    return success_response(user.serialize(),201)

@app.route("/")
@app.route("/api/users/")
def get_users():
    """
    Endpoint for getting all users
    """
    users = [user.serialize() for user in User.query.all()]
    return success_response({"users" : users})

@app.route("/")
@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting an user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())

@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """
    Endpoint for deleting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    curr_user = user.serialize().copy()
    db.session.delete(user)
    db.session.commit()
    return success_response(curr_user)

@app.route("/api/rides/<int:ride_id>/add/", methods=["POST"])
def assign_passenger(ride_id):
    """
    Endpoint for assigning a user
    to a ride by id
    """
    ride = Ride.query.filter_by(id = ride_id).first()
    if ride is None:
        return failure_response("Ride not found!")
    if ride.seats_open < 1:
        return failure_response("No more open seats in the ride!")
    body = json.loads(request.data)
    user_id = body.get("user_id")

    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    if user in ride.passengers or user == ride.driver:
        return failure_response("User is already in ride!")

    ride.passengers.append(user)
    ride.seats_open -= 1
    db.session.commit()
    return success_response(ride.serialize())

@app.route("/api/rides/<int:ride_id>/remove/", methods=["DELETE"])
def remove_passenger(ride_id):
    """
    Endpoint for removing an user
    from a ride by id
    """
    ride = Ride.query.filter_by(id = ride_id).first()
    if ride is None:
        return failure_response("Ride not found!")

    body = json.loads(request.data)
    user_id = body.get("user_id")

    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    if user == ride.driver:
        return failure_response("User is the driver!")

    ride.passengers.remove(user)
    ride.seats_open += 1
    db.session.commit()
    return success_response(ride.serialize())
    
#Login routes

def extract_token(request):
    """
    helper method for extracting the token
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("missing auth header")
    bearer_token = auth_header.replace("Bearer", "").strip()
    if not bearer_token:
        return False, failure_response("invalid auth header")
    return True, bearer_token


@app.route("/api/login/", methods=["POST"])
def login():
    """
    Endpoint for login a user in using their username and password
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return failure_response("Invalid email or password", 400)

    sucess, user = users_dao.verify_credentials(email, password)

    if not sucess:
        return failure_response("Incorrect email or password", 400)
    return json.dumps(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )


@app.route("/api/logout/", methods=["POST"])
def logout():
    """
    Endpoint for loggin out a user
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return failure_response("invalid session token", 400)
    user.session_expiration = datetime.datetime.now()
    db.session.commit()
    return json.dumps({"message": "user successfully logged out"})


@app.route("/api/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updateing a user's session using the refresh token
    """
    success, update_token = extract_token(request)
    if not success:
        return update_token
    user = users_dao.renew_session(update_token)
    if user is None:
        return failure_response("invalid update token")
    return json.dumps(
        {
            "session_token": user.session_token,
            "session_expiration": str(user.session_expiration),
            "update_token": user.update_token
        }
    )


@app.route("/api/secret/", methods=["POST"])
def secret_message():
    """
    Endpoint for verifying the session token and returning a secret message
    """
    sucess, session_token = extract_token(request)
    if not sucess:
        return session_token
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or user.verify_session_token(session_token):
        return failure_response("invalid session token")
    return json.dumps({"message": "Implemented session token"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
