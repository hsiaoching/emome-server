from flask import Flask
from flask.ext.pymongo import PyMongo
from flask import request
from datetime import datetime
import simplejson
from bson.json_util import dumps
from bson import json_util
from bson.objectid import ObjectId
from flask.ext.api import status
from flask_restful import Resource, Api, reqparse
import json


EMOTION_SAD = 'sad'
EMOTION_FRUSTRATED = 'frustrated'
EMOTION_ANGRY = 'angry'
EMOTION_ANXIOUS = 'anxious'


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'primer'
mongo = PyMongo(app,config_prefix='MONGO')
api = Api(app)



'''
Login: 
    login[post: user_id, name]

Suggestion: 
    see suggestion[get: message, content]
    make suggestion[post to suggestion table: user_id, emotion, scenario_id, message, content]

SuggestionImpact:
    see effect[get:impact]    

History:
    take action[post to history table: user_id, suggestion_id, emotion, scenario_id]
    give feedback[put: history_id, rating, feedback]
'''


def to_json(data):
    return json.dumps(data, default=json_util.default)


login_parser = reqparse.RequestParser()
login_parser.add_argument('_id', type=str)
login_parser.add_argument('name', type=str)

class Login(Resource):

    # facebook login
    def post(self):            
        args = login_parser.parse_args()
        if mongo.db.users.find({'_id': args['_id']}).count() == 0:
            mongo.db.users.insert_one({
                '_id': args['_id'],
                'name': args['name'],
                'join_time': datetime.now()
            })
            return {'status': "new user"}
        else:
            return {'status': "existing user"}

with app.app_context():
    num_scenarios = mongo.db.scenarios.count()

suggestion_parser = reqparse.RequestParser()
suggestion_parser.add_argument('user_id', type=str)
suggestion_parser.add_argument('emotion', type=dict, choices=range(11))
suggestion_parser.add_argument('scenario_id', type=int, choices=range(num_scenarios))
suggestion_parser.add_argument('content', type=str)
suggestion_parser.add_argument('message', type=str)

class Suggestion(Resource):

    # see suggestion
    def get(self):
        return to_json({'status': "under construction..."})

    # make suggestion
    def post(self):
        args = suggestion_parser.parse_args() 
        
        # check if the user exists
        if validate_user(args['user_id']) == False:
            print("unregistered user")
            return to_json({'err_msg': "unregistered user"}), status.HTTP_403_FORBIDDEN

        object_id = str(ObjectId())
        mongo.db.suggestions.insert_one({
            '_id': object_id,
            'user_id': args['user_id'],
            'emotion': {
                EMOTION_SAD: int(args['emotion'][EMOTION_SAD]),
                EMOTION_FRUSTRATED: int(args['emotion'][EMOTION_FRUSTRATED]),
                EMOTION_ANGRY: int(args['emotion'][EMOTION_ANGRY]),
                EMOTION_ANXIOUS: int(args['emotion'][EMOTION_ANXIOUS])
            },
            'scenario_id': int(args['scenario_id']),
            'time': datetime.now(),
            'content': args['content'],
            'message': args['message'],
            'impact': None
        })
        return to_json({'_id': object_id, 'status': "success"})

def validate_user(user_id):
    if mongo.db.users.find({'_id': user_id}).count() == 0:
        # unregistered uesr
        return False
    else:
        # registered user
        return True


'''
def validate_emotion(emotion):
    if not (0 <= emotion[EMOTION_SAD] <= 10) \
    or not (0 <= emotion[EMOTION_FRUSTRATED] <= 10) \
    or not (0 <= emotion[EMOTION_ANGRY] <= 10) \
    or not (0 <= emotion[EMOTION_ANXIOUS] <= 10):
        return False
    else:
        return True

def validate_scenario(scenario_id):
    scenario_id = int(scenario_id)
    if not (0 <= scenario_id < mongo.db.scenarios.count()):
        # invalid scenario id
        return False
    else:
        # valid scenario id
        return True

def validate_suggestion(suggestion_id):
    if mongo.db.suggestions.find({'_id': suggestion_id}).count() == 0:
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
            print("invalid emotion values")
            return to_json({'err_msg': "invalid emotion values"}),status.HTTP_403_FORBIDDEN

        # check if the user exists
        if validate_user(request.form['user_id']) == False:
            print("unregistered user")
            return to_json({'err_msg': "unregistered user"}), status.HTTP_403_FORBIDDEN

        # check if the scenario exists
        if validate_scenario(request.form['scenario_id']) == False:    
            print("invalid scenario")
            return to_json({'err_msg': "invalid scenario"}), status.HTTP_403_FORBIDDEN
        
        object_id = str(ObjectId())
        mongo.db.suggestions.insert_one({
            '_id': object_id,
            'user_id': request.form['user_id'],
            'emotion': {
                EMOTION_SAD: int(emotions[EMOTION_SAD]),
                EMOTION_FRUSTRATED: int(emotions[EMOTION_FRUSTRATED]),
                EMOTION_ANGRY: int(emotions[EMOTION_ANGRY]),
                EMOTION_ANXIOUS: int(emotions[EMOTION_ANXIOUS])
            },
            'scenario_id': int(request.form['scenario_id']),
            'time': datetime.now(),
            'content': request.form['content'],
            'message': request.form['message'],
            'impact': None
        })
        return to_json({'_id': object_id, 'status': "success"})
    else:
        return to_json({'status': "fail"})

@app.route('/take_suggestion', methods=['POST'])
def take_suggestion():
    if request.method == 'POST':
        emotions = simplejson.loads(str(request.form['emotion']))

        # check if the user exists
        if validate_user(request.form['user_id']) == False:
            print("unregistered user")
            return to_json({'err_msg': "unregistered user"}), status.HTTP_403_FORBIDDEN

        # check if the suggestion id is valid
        if validate_suggestion(request.form['suggestion_id']) == False:
            print("invalid suggestion id")
            return to_json({'err_msg': "invalid suggestion id"}), status.HTTP_403_FORBIDDEN

        object_id = str(ObjectId())
        mongo.db.histories.insert_one({
            '_id': object_id,
            'user_id': request.form['user_id'],
            'time': datetime.now(),
            'suggestion_id': request.form['suggestion_id'],
            'emotion': {
                EMOTION_SAD: emotions[EMOTION_SAD],
                EMOTION_FRUSTRATED: emotions[EMOTION_FRUSTRATED],
                EMOTION_ANGRY: emotions[EMOTION_ANGRY],
                EMOTION_ANXIOUS: emotions[EMOTION_ANXIOUS]
            },
            'scenario_id': int(request.form['scenario_id']),
            'rating': None,
            'feedback': None
        })
        return to_json({'_id': object_id, 'status': "success"})
    else:
        return to_json({'status': "fail"})
'''


api.add_resource(Login, '/login')
api.add_resource(Suggestion, '/suggestion')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
