import requests

from django.db import connection

KEY = 'monhygdsolgfdigfden'


class Slacker():

    def __init__(self, webhook=None):
        self.webhook_url = webhook

    def send(self, msg=None, channel='#general'):
        payload = {
            "text": msg,
            "channel": channel
        }
        requests.post(self.webhook_url, json=payload)


def query_nb_submissions(user_id):
    cursor = connection.cursor()
    return list(cursor.execute('SELECT COUNT(*) FROM submissions WHERE valid = 0 and by_id={};'.format(int(user_id))))[0][0]


def query_best_submission():
    cursor = connection.cursor()
    best_submission = cursor.execute('''
        SELECT min(submissions.score) as best_score, teams.name, persons.first_name || " " || UPPER(persons.last_name) as full_name
        FROM submissions, teams, persons
        WHERE submissions.team_id = teams.id AND submissions.by_id = persons.id;
    ''')
    return list(best_submission)[0]

Candidat = KEY[0:3] + KEY[5] + KEY[8:10] + KEY[13] + KEY[17:20]
