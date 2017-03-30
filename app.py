import os
from flask import Flask, jsonify, request
from faker import Factory
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import (
    SyncGrant,
    VideoGrant,
    IpMessagingGrant
)
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname


app = Flask(__name__)
fake = Factory.create()
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/video/')
def video():
    return app.send_static_file('video/index.html')

@app.route('/sync/')
def sync():
    return app.send_static_file('sync/index.html')

@app.route('/notify/')
def notify():
    return app.send_static_file('notify/index.html')

@app.route('/chat/')
def chat():
    return app.send_static_file('chat/index.html')

# Basic health check - check environment variables have been configured
# correctly
@app.route('/config')
def config():
    return jsonify(
        TWILIO_ACCOUNT_SID=os.environ['TWILIO_ACCOUNT_SID'],
        TWILIO_NOTIFICATION_SERVICE_SID=os.environ['TWILIO_NOTIFICATION_SERVICE_SID'],
        TWILIO_API_KEY=os.environ['TWILIO_API_KEY'],
        TWILIO_API_SECRET=bool(os.environ['TWILIO_API_SECRET']),
        TWILIO_CHAT_SERVICE_SID=os.environ['TWILIO_CHAT_SERVICE_SID'],
        TWILIO_SYNC_SERVICE_SID=os.environ['TWILIO_SYNC_SERVICE_SID'],
        TWILIO_CONFIGURATION_SID=os.environ['TWILIO_CONFIGURATION_SID']
    )

@app.route('/token')
def token():
    # get credentials for environment variables
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    api_key = os.environ['TWILIO_API_KEY']
    api_secret = os.environ['TWILIO_API_SECRET']
    sync_service_sid = os.environ['TWILIO_SYNC_SERVICE_SID']
    chat_service_sid = os.environ['TWILIO_CHAT_SERVICE_SID']


    # create a randomly generated username for the client
    identity = fake.user_name()

    # Create access token with credentials
    token = AccessToken(account_sid, api_key, api_secret, identity)

    # Create a Sync grant and add to token
    if sync_service_sid:
        sync_grant = SyncGrant(service_sid=sync_service_sid)
        token.add_grant(sync_grant)

    # Create a Video grant and add to token
    video_grant = VideoGrant(room='default_room')
    token.add_grant(video_grant)

    # Create an Chat grant and add to token
    if chat_service_sid:
        chat_grant = IpMessagingGrant(service_sid=chat_service_sid)
        token.add_grant(chat_grant)

    # Return token info as JSON
    return jsonify(identity=identity, token=token.to_jwt())

# Notify - create a device binding from a POST HTTP request
@app.route('/register', methods=['POST'])
def register():
    # get credentials for environment variables
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    api_key = os.environ['TWILIO_API_KEY']
    api_secret = os.environ['TWILIO_API_SECRET']
    service_sid = os.environ['TWILIO_NOTIFICATION_SERVICE_SID']

    # Initialize the Twilio client
    client = Client(api_key, api_secret, account_sid)

    # Body content
    content = request.get_json()

    # Get a reference to the notification service
    service = client.notify.services(service_sid)

    # Create the binding
    binding = service.bindings.create(
        endpoint=content["endpoint"],
        identity=content["identity"],
        binding_type=content["BindingType"],
        address=content["Address"])

    print(binding)

    # Return success message
    return jsonify(message="Binding created!")

# Notify - send a notification from a POST HTTP request
@app.route('/send-notification', methods=['POST'])
def send_notification():
    # get credentials for environment variables
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    api_key = os.environ['TWILIO_API_KEY']
    api_secret = os.environ['TWILIO_API_SECRET']
    service_sid = os.environ['TWILIO_NOTIFICATION_SERVICE_SID']

    # Initialize the Twilio client
    client = Client(api_key, api_secret, account_sid)

    service = client.notify.services(service_sid)

    # Create a notification for a given identity
    identity = request.form.get('identity')
    notification = service.notifications.create(
        identity=identity,
        body='Hello ' + identity + '!'
    )

    return jsonify(message="Notification created!")

@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True)
