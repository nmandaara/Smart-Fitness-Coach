from pydantic import BaseModel
from typing import List

# Base Model for workouts, all the required fields are mentioned
class Workout(BaseModel):
    username: str
    date: str
    muscle: str
    exercises: List[str]
    duration: int
    calories_burned: int

# Base Model for Users, all the required fields are mentioned. 
class User(BaseModel):
    username: str
    email: str
    name: str
    age: int
    weight: int

class User_History(BaseModel):
    username: str
    current_weight: int # User must enter
    date: str

# Base Model for the questions from users. 
class ChatRequest(BaseModel):
    question:str

# future I would like to expand to have daily food intake
# class Food(BaseModel):
#     protein: int
#     carbs: int
#     fat: int
#     dish: str
#     meal_type: str
#     date:str