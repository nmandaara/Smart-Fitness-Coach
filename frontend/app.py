from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import logging
import re
import json

logger = logging.getLogger()
handler = logging.StreamHandler()
format = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


app = Flask(__name__)
app.secret_key = "supersecretkey"

def parse_recommendations(recommendations):
    logger.info("THIS IS RECOMMENDATIONS PARSING")
    logger.info(recommendations)
    intro = re.search(r"(.+?)Day", recommendations, re.DOTALL).group(1).strip()
    
    # Split the text by days
    days = re.split(r"(Day \d+:)", recommendations)
    structured_recommendations = []

    for i in range(1, len(days), 2):
        day = days[i]
        exercises = [e.strip() for e in days[i + 1].strip().split('\n')]
        structured_recommendations.append((day, exercises))

    return intro, structured_recommendations

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ask')
def ask():
    question = request.form['question']
    response = request.post('https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/chat', json = {'question':question})
    answer = response.json().get('answer')
    return jsonify({'answer':answer})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'email': request.form['email'],
            'name': request.form['name'],
            'age': request.form['age'],
            'weight': request.form['current_weight']
        }
        logger.info(f"Data from the form is {data}")
        response = requests.post('https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/add_user', json=data)

        if response.status_code == 200:
            flash('User registered successfully!')
        else:
            flash('Failed to register user')
        return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/add_workout', methods=['GET', 'POST'])
def add_workout():
    if request.method == 'POST':
        username = request.form['username']
        date = request.form['date']
        muscle = request.form['muscle']
        exercises = request.form['exercises'].split(',')
        exercises = [exercise.strip() for exercise in exercises]
        duration = int(request.form['duration'])
        calories_burned = int(request.form['calories_burned'])

        data = {
            "username": username,
            "date": date,
            "muscle": muscle,
            "exercises": exercises,
            "duration": duration,
            "calories_burned": calories_burned
        }

        response = requests.post('https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/add_workout', json=data)
        if response.status_code == 200:
            flash('Workout Entered successfully!')
        else:
            flash('Failed to enter workout. ')
            return redirect(url_for('add_workout'))
    return render_template('add_workout.html')

@app.route('/recommendations', methods = ['GET','POST'])
def recommendations():
    if request.method == 'POST':
        user = request.form['username']
        logger.info("inside rec")
        if not user:
            flash('Username is required')
            logger.info("user not found")
            return redirect(url_for('home'))
        url = f'https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/get_recommendations/{user}'
        try:
            response = requests.get(url)
            response.raise_for_status
            data = response.json()
            intro, structured_recommendations = parse_recommendations(data["recommendations"])
            return render_template('recommendations.html', username=user, intro=intro, structured_recommendations=structured_recommendations)
        except requests.RequestException as e:
            flash(f"Error fetching recommendations: {e}")
            return redirect(url_for('home'))
    else:
        return render_template('recommendations.html')

@app.route('/similar_users_weight', methods = ['GET','POST'])
def similar_users_weight():
    if request.method == 'POST':
        user = request.form['username']
        logger.info("inside rec")
        if not user:
            flash('Username is required')
            logger.info("user not found")
            return redirect(url_for('home'))
        url = f'https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/similar_users_weight/{user}'
        try:
            response = requests.get(url)
            response.raise_for_status
            data = response.json()["similar_users"]
            logger.info(response)
            logger.info(data)
            return render_template("similar_users_weight.html", data=data)
        except requests.RequestException as e:
            flash(f"Error fetching Similar Users: {e}")
            return redirect(url_for('home'))
    else:
        return render_template('similar_users_weight.html')

@app.route('/similar_users_by_workout', methods = ['GET','POST'])
def similar_users_by_workout():
    if request.method == 'POST':
        user = request.form['username']
        logger.info("inside rec")
        if not user:
            flash('Username is required')
            logger.info("user not found")
            return redirect(url_for('home'))
        url = f'https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/similar_users_workout/{user}'
        try:
            response = requests.get(url)
            response.raise_for_status
            data = response.json()["similar_users"]
            logger.info(response)
            logger.info(data)
            return render_template("similar_users_by_workout.html", data=data)
        except requests.RequestException as e:
            flash(f"Error fetching Similar Users: {e}")
            return redirect(url_for('home'))
    else:
        return render_template('similar_users_by_workout.html')

# @app.route('/chat')
# def chat():
#     return render_template('chat.html')

messages = [
    {"sender": "bot", "text": "Hello! How can I help you today?"},
]

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    bot_response = ""
    if request.method == "POST":
        user_message = request.form['message']
        messages.append({"sender": "user", "text": user_message})

        payload = {
            "question":user_message
        }
        messages.append({"sender": "bot", "text": bot_response})

        url = f'https://smartfitnesscoach-api.salmonrock-3f6a95ca.eastus.azurecontainerapps.io/chat_db/'
        try:
            response = requests.post(url,  data = json.dumps(payload))
            logger.info(response)
            if response.status_code == 200:
                bot_response = response.text.replace('"','')
            else:
                bot_response = 'Error communicating with the API'
        except requests.exceptions.RequestException as e:
            bot_response = f"Request failed : {e}"
        
        messages.append({"sender":"bot", "text": bot_response})
        return render_template('chat.html', messages=messages)
    return render_template('chat.html', messages=messages)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
