import requests
import json

def workouts():
    with open("User_Workouts.json","r") as file:
        data = json.load(file)


    for workout in data:
        response = requests.post("http://localhost:8000/add_workout", json=workout)
        print(f"Status Code: {response.status_code}, Response: {response.json()}")

    print("ALL WORKOUTS ENTERED")

def users():
    with open("Users.json", "r") as file:
        users = json.load(file)
    
    for user in users:
        response = requests.post("http://localhost:8000/add_user", json=user)
        print(f"Status Code: {response.status_code}, Response: {response.json()}")
    
    print("ALL USERS ENTERED")

def weight():
    print("RUNNING WEIGHTS")
    with open("User_History.json", "r") as file:
        user_history = json.load(file)
    
    for user in user_history:
        response = requests.post("http://localhost:8000/weight_entry", json=user)
        print(f"Status Code: {response.status_code}, Response: {response.json()}")

    print("ALL WEIGHTS CAPTURED")
if __name__ == "__main__":
    users()
    workouts()
    weight()

