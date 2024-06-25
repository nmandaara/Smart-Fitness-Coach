from fastapi import APIRouter, HTTPException
from app.models import Workout, User, ChatRequest, User_History
from app.utils import add_user, add_workout, fetch_user, generate_recommendation, similar_users_weight, similar_users_workouts, chat, chat_db, user_history
import logging

# Logger initialization
logger = logging.getLogger()
handler = logging.StreamHandler()
format = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
router = APIRouter()

# Root URL
@router.get('/')
def home():
    return "Welcome to Smart Fitness Coach!"

# Adds a user, if there is a user in DB, it throws error
# User details must match with the User Model
@router.post("/add_user")
def rt_add_user(user: User):
    existing_user = fetch_user(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    add_user(user)
    return {"message": "User added successfully"}

# Adds a workout per user, for a particular date. 
# This can contain many users. But user must exist in DB. 
@router.post("/add_workout")
def rt_add_workout(workout: Workout):
    user = fetch_user(workout.username)
    if not user:
        raise HTTPException(status_code = 404, detail="User not found")
    username = user["user"]["username"]
    add_workout(username, workout)
    return {"message": "Workout added successfully"}

# To check the users in the DB by username
@router.get("/get_user/{username}")
def rt_get_user(username: str):
    user = fetch_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# This uses AI to get the recommendations based on users weight, workout history
@router.get("/get_recommendations/{username}")
def rt_get_recommendations(username: str):
    recommendations = generate_recommendation(username)
    return {"recommendations": recommendations}

# Returns the list of users who are similar in weight compared to the queried user
@router.get("/similar_users_weight/{username}")
def rt_similar_users_weight(username: str):
    similar_users_weight_out = similar_users_weight(username)
    return {"similar_users": similar_users_weight_out}

# Based on the workout history, this returns the list of users.
@router.get("/similar_users_workouts/{username}/{workout}")
def rt_similar_users_workout(username: str, workout: str):
    similar_users_workout_out = similar_users_workouts(username, workout)
    return {"similar_users": similar_users_workout_out}

# Chat is a random chat object to get your fitness questions answered . Not linked to db
@router.post("/chat")
def rt_chat(request: ChatRequest) -> str:
    if not request.question:
        raise HTTPException(status_code=400, detail="Field Required")
    logger.info(f"question is {request.question}")
    answer = chat(request.question)
    return answer

# Chat DB is Vector search on Database. 
@router.post("/chat_db")
def rt_chat(request: ChatRequest) -> str:
    if not request.question:
        raise HTTPException(status_code=400, detail="Field Required")
    logger.info(f"question is {request.question}")
    answer = chat_db(request.question)
    return answer

# For entering current weight details
@router.post("/weight_entry")
def rt_weight_entry(user_details: User_History):
    existing_user = fetch_user(user_details.username)
    if not existing_user:
        raise HTTPException(status_code=400, detail="User is not in DB")
    username = existing_user["user"]["username"]
    user_history(username, user_details)
    return {"message": "User added successfully"}