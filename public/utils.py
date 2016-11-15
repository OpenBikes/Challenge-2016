import requests


class Slacker():

    def __init__(self, webhook=None):
        self.webhook_url = webhook

    def send(self, msg=None, channel='#general'):
        payload = {
            "text": msg,
            "channel": channel
        }
        requests.post(self.webhook_url, json=payload)

Candidat = 'mongolien'
