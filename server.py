from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
import os
import json
import threading
import time
import datetime

data_folder = '/home/xavier/Personal/MurderMystery/data'
moordspel_folder = '/home/xavier/Personal/MurderMystery/moordspel_data'

class ServerBackend():
    def __init__(self):
        self.question_data = {}
        self.code_values = {}

        self.load_data_info()

    def load_data_info(self):
        folder_path = "moordspel_data"

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ids = [value["id"] for value in data.values() if "id" in value]
                    key = filename.replace(".json", "")
                    self.question_data[key] = {"ids": ids}

    def check_progress(self, category, team_name):
        ids = self.question_data[category]["ids"]

        team_path = os.path.join(data_folder, (str(team_name) + '.json'))

        with open(team_path, "r") as json_file:
            existing_data = json.load(json_file)
        
        for id in ids:
            if id in existing_data["questions"]:
                pass
            else:
                return None
        return 'success'
        
    # Function to get the list of teams and their progress from the data folder
    def get_team_data(self):
        team_data = {}
        for file_name in os.listdir(data_folder):
            if file_name.endswith(".json"):
                team_name = file_name.replace(".json", "")
                file_path = os.path.join(data_folder, file_name)
                with open(file_path, "r") as json_file:
                    team_info = json.load(json_file)
                    team_data[team_name] = team_info.get('progress', 0)  # Default progress is 0
        return team_data

    # Function to simulate a long-running task and update team progress
    def long_running_task(self, team_name):
        file_path = os.path.join(data_folder, f"{team_name}.json")
        # for i in range(1, 101):  # Simulate progress from 1% to 100%
        #     time.sleep(0.1)  # Simulating a task (could be replaced with real task)
        #     with open(file_path, "r") as json_file:
        #         team_data = json.load(json_file)
        #     team_data['progress'] = i  # Update the progress
        #     with open(file_path, "w") as json_file:
        #         json.dump(team_data, json_file, indent=4)
        pass

    def answer_question(self, location, question_id, answer, team_name):
        file_path = os.path.join(moordspel_folder, (str(location) + '.json'))
        moordspel_data = {}
        if os.path.exists(file_path):
            # If the file exists, open and read the existing data
            with open(file_path, "r") as json_file:
                moordspel_data = json.load(json_file)
        
        for key in moordspel_data.keys():
            if moordspel_data[key]['id'] == question_id:
                answers = []
                for i in moordspel_data[key]['answer']:
                    i = i.strip().lower()
                    answers.append(i)

                if answer.strip().lower() in answers:
                    status = 'correct'

                    team_path = os.path.join(data_folder, (str(team_name) + '.json'))

                    with open(team_path, "r") as json_file:
                        existing_data = json.load(json_file)
                    
                    if not question_id in existing_data['questions']:
                        existing_data['questions'].append(question_id)
                        existing_data['progress'] += 1
                        existing_data['code_values'][question_id] = moordspel_data[key]['code']
                    else:
                        print("Already in set")
                    
                    with open(team_path, "w") as json_file:
                        json.dump(existing_data, json_file, indent=4)
                else:
                    status = 'incorrect'

                return moordspel_data[key], status
        
        return None  # If no match is found, return None after the loop finishes

    def update_questions(self, location, team_name):
        answers_status = {}
        answer_dict = {}
        question_desc = {}

        file_path = os.path.join(moordspel_folder, (str(location) + '.json'))
        moordspel_data = {}
        if os.path.exists(file_path):
            # If the file exists, open and read the existing data
            with open(file_path, "r") as json_file:
                moordspel_data = json.load(json_file)
        
        team_path = os.path.join(data_folder, (str(team_name) + '.json'))

        with open(team_path, "r") as json_file:
            existing_data = json.load(json_file)

        for key in moordspel_data.keys():
            question_desc[moordspel_data[key]['id']] = moordspel_data[key]['description']
            
            if moordspel_data[key]['id'] in existing_data['questions']:
                answers_status[moordspel_data[key]['id']] = 'correct'
                answer_dict[moordspel_data[key]['id']] = ' / '.join(moordspel_data[key]['answer'])
            else:
                answers_status[moordspel_data[key]['id']] = 'incorrect'

        return answers_status, answer_dict, question_desc

server_backend = ServerBackend()

app = Flask(__name__)

@app.route("/")
def home():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams
        return render_template("welkom.html", team=team_name, teams=team_data)
    else:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams
        return render_template("welkom.html", teams=team_data)

@app.route("/welkom", methods=["POST"])
def welkom():
    team = str(request.form.get("team")).lower()
    password = str(request.form.get("password"))
    
    # Define file name based on the team name
    file_name = f"{team}.json"
    file_path = os.path.join(data_folder, file_name)
    
    # Check if the file already exists
    if os.path.exists(file_path):
        # If the file exists, open and read the existing data
        with open(file_path, "r") as json_file:
            existing_data = json.load(json_file)
        
        # Check if the password matches
        if existing_data.get('password') == password:
            # Password matches, so proceed with the request
            if existing_data['last_page']:
                pass
            else:
                existing_data['last_page'] = 'overzicht'

            with open(file_path, "w") as json_file:
                json.dump(existing_data, json_file, indent=4)

            # Set the team name in the cookies for future use
            response = make_response(render_template(existing_data['last_page'] + ".html", response="Password matches! Welcome.", team=team, teams=server_backend.get_team_data()))
            response.set_cookie('team_name', team)
            return response
        else:
            # Password does not match
            return render_template("welkom.html", response="Incorrect password. Please try again.")
    
    else:
        # If the file does not exist, create the data
        data = {
            'team': team,
            'password': password,
            'last_page' : 'overzicht',
            'progress': 0,  # Initialize progress to 0
            'questions': [],
            "code_values": {},
        }
        
        # Make sure the folder exists
        os.makedirs(data_folder, exist_ok=True)
        
        # Write the data to a new file
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        # Set the team name in the cookies for future use
        response = make_response(render_template(data['last_page'] + ".html", response="Team data saved successfully!", team=team, teams=server_backend.get_team_data()))
        response.set_cookie('team_name', team)
        return response

@app.route("/overzicht")
def overzicht():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams
        server_backend.code_values = ["*", "*", "*", "*", "*", "*", "*", "*"]
        
        team_path = os.path.join(data_folder, (str(team_name) + '.json'))

        with open(team_path, "r") as json_file:
            existing_data = json.load(json_file)

        show_code = False
        if show_code:
            for key in existing_data['code_values'].keys():
                server_backend.code_values[int(key) - 1] = existing_data['code_values'][key]

        return render_template("overzicht.html", team=team_name, teams=team_data, code_values=server_backend.code_values)
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page

@app.route("/woonkamer_vragen", methods=["GET", "POST"])
def woonkamer_vragen():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    answers_status = {}  # Initialize the answers_status dictionary
    answer_dict = {}
    location = 'woonkamer_vragen'

    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams

        # Check answer status for the team
        answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)
        if request.method == "POST":
            question_id = int(request.form['question_id'])  # Get the question id
            answer = request.form['answer']  # Get the submitted answer

            _, status = server_backend.answer_question(location, question_id, answer, team_name)

            if status == 'correct':
                answers_status[question_id] = 'correct'
                answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)
            else:
                answers_status[question_id] = 'incorrect'

        # After processing the answer or for the initial page load, render the page with the answers_status
        return render_template("woonkamer_vragen.html", team=team_name, teams=team_data, answers_status=answers_status, answer_dict=answer_dict, question_desc=question_desc)
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page

@app.route("/woonkamer_artiest", methods=["GET", "POST"])
def woonkamer_artiest():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    answers_status = {}  # Initialize the answers_status dictionary
    answer_dict = {}
    location = 'woonkamer_artiest'

    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams

        # Check answer status for the team
        answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)
        if request.method == "POST":
            question_id = int(request.form['question_id'])  # Get the question id
            answer = request.form['answer']  # Get the submitted answer

            _, status = server_backend.answer_question(location, question_id, answer, team_name)

            if status == 'correct':
                answers_status[question_id] = 'correct'
                answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)
            else:
                answers_status[question_id] = 'incorrect'

        # After processing the answer or for the initial page load, render the page with the answers_status
        return render_template("woonkamer_artiest.html", team=team_name, teams=team_data, answers_status=answers_status, answer_dict=answer_dict, question_desc=question_desc)
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page

@app.route("/woonkamer")
def woonkamer():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams

        artist_unlocked = server_backend.check_progress("woonkamer_artiest", team_name)
        image_unlocked = server_backend.check_progress("woonkamer_vergelijk", team_name)
        flask_unlocked = server_backend.check_progress("woonkamer_periodieksysteem", team_name)
        camera_unlocked = server_backend.check_progress("woonkamer_vroeger", team_name)
        lottery_unlocked = server_backend.check_progress("woonkamer_nummers", team_name)
        research_unlocked = server_backend.check_progress("woonkamer_vragen", team_name)
                
        return render_template(
            "woonkamer.html",
            team=team_name,
            teams=team_data,
            artist_unlocked=artist_unlocked,
            image_unlocked=image_unlocked,
            flask_unlocked=flask_unlocked,
            camera_unlocked=camera_unlocked,
            lottery_unlocked=lottery_unlocked,
            research_unlocked=research_unlocked,
        )
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page

@app.route("/tuin")
def tuin():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams
        return render_template("tuin.html", team=team_name, teams=team_data)
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page

@app.route("/gang", methods=["GET", "POST"])
def gang():
    team_name = request.cookies.get('team_name')  # Get the team name from the cookie
    answers_status = {}  # Initialize the answers_status dictionary
    answer_dict = {}
    location = 'gang'

    if team_name:
        team_data = server_backend.get_team_data()  # Get the current progress for all teams

        # Check answer status for the team
        answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)

        if request.method == "POST":
            question_id = int(request.form['question_id'])  # Get the question id
            answer = request.form['answer']  # Get the submitted answer

            _, status = server_backend.answer_question(location, question_id, answer, team_name)

            if status == 'correct':
                answers_status[question_id] = 'correct'
                answers_status, answer_dict, question_desc = server_backend.update_questions(location, team_name)
            else:
                answers_status[question_id] = 'incorrect'

        # After processing the answer or for the initial page load, render the page with the answers_status
        return render_template("gang.html", team=team_name, teams=team_data, answers_status=answers_status, answer_dict=answer_dict, question_desc=question_desc)
    else:
        return redirect(url_for('home'))  # If no team is logged in, redirect to home page


# Route to get the current progress of all teams
@app.route('/progress')
def get_progress():
    team_data = server_backend.get_team_data()  # Get the current progress for all teams
    return jsonify(team_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
