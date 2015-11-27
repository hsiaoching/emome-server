from flask import Flask
from flask.ext.pymongo import PyMongo
from flask import request
from datetime import datetime
import simplejson
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask.ext.api import status

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'primer'
mongo = PyMongo(app,config_prefix='MONGO')

@app.route('/fb_login', methods=['POST'])
def login():
    if request.method == 'POST':
        if mongo.db.users.find({"_id": request.form['fb_id']}).count() == 0:
            mongo.db.users.insert_one({
                "_id": request.form['fb_id'],
                "name": request.form['name'],
                "join_time": datetime.now()
            })
            return dumps({"status": "new user"})
        else:
            return dumps({"status": "existing user"})

def validate_user(user_id):
    if mongo.db.users.find({"_id": user_id}).count() == 0:
        # unregistered uesr
        return False
    else:
        # registered user
        return True

def validate_emotion(emotion):
    if emotion["sad"] < 0 or emotion["sad"] > 10 \
    or emotion["frustrated"] < 0 or emotion["frustrated"] > 10 \
    or emotion["angry"] < 0 or emotion["angry"] > 10 \
    or emotion["fearful"] < 0 or emotion["fearful"] > 10:
        return False
    else:
        return True

def validate_scenario(scenario_id):
    scenario_id = int(scenario_id)
    if scenario_id < 0 or scenario_id >= mongo.db.scenarios.count():
        # invalid scenario id
        return False
    else:
        # valid scenario id
        return True

def validate_suggestion(suggestion_id):
    if mongo.db.suggestions.find({"_id": suggestion_id}).count() == 0:
        # invalid suggestion id
        return False
    else:
        # valid suggestion id
        return True

@app.route('/make_suggestion', methods=['POST'])
def make_suggestion():
    if request.method == 'POST':
        emotions = simplejson.loads(str(request.form['emotion']))
         
        # check if emotion values are between 0 ~ 10
        if validate_emotion(emotions) == False:
            print "invalid emotion values"
            return dumps({"invalid emotion values"}),status.HTTP_403_FORBIDDEN

        # check if the user exists
        if validate_user(request.form["user_id"]) == False:
            print "unregistered user"
            return dumps({"unregistered user"}), status.HTTP_403_FORBIDDEN

        # check if the scenario exists
        if validate_scenario(request.form["scenario_id"]) == False:    
            print "invalid scenario"
            return dumps({"invalid scenario"}), status.HTTP_403_FORBIDDEN
        
        object_id = str(ObjectId())
        mongo.db.suggestions.insert_one({
            "_id": object_id,
            "user_id": request.form['user_id'],
            "emotion": {
                "sad": int(emotions['sad']),
                "frustrated": int(emotions['frustrated']),
                "angry": int(emotions['angry']),
                "fearful": int(emotions['fearful'])
            },
            "scenario_id": int(request.form['scenario_id']),
            "time": datetime.now(),
            "content": request.form['content'],
            "message": request.form['message'],
            "impact": None
        })
        return dumps({"_id": object_id, "status": "success"})
    else:
        return dumps({"status": "fail"})

@app.route('/take_suggestion', methods=['POST'])
def take_suggestion():
    if request.method == 'POST':
        emotions = simplejson.loads(str(request.form['emotion']))

        # check if the user exists
        if validate_user(request.form["user_id"]) == False:
            print "unregistered user"
            return dumps({"unregistered user"}), status.HTTP_403_FORBIDDEN

        # check if the suggestion id is valid
        if validate_suggestion(request.form["suggestion_id"]) == False:
            print "invalid suggestion id"
            return dumps({"invalid suggestion id"}), status.HTTP_403_FORBIDDEN

        object_id = str(ObjectId())
        mongo.db.histories.insert_one({
            "_id": object_id,
            "user_id": request.form['user_id'],
            "time": datetime.now(),
            "suggestion_id": request.form['suggestion_id'],
            "emotion": {
                "sad": emotions['sad'],
                "frustrated": emotions['frustrated'],
                "angry": emotions['angry'],
                "fearful": emotions['fearful']
            },
            "scenario_id": int(request.form["scenario_id"]),
            "rating": None,
            "feedback": None
        })
        return dumps({"_id": object_id,"status": "success"})
    else:
        return dumps({"status": "fail"})

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
