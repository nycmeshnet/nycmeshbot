import dateutil.parser, datetime, os, json, requests
from jinja2 import Environment, FileSystemLoader
import app.slackapi as slack


class AcuityHandlers:

    def __init__(self, current_app):
    	self.config = current_app

	self.USER_ID = self.config['ACUITY_USER_ID']
	self.API_KEY = self.config['ACUITY_API_KEY']

	#Prep jinja2 templates for whole class
	file_loader = FileSystemLoader(os.path.dirname(os.path.abspath(__file__)) + '/../templates/acuity')
	# Load the enviroment
	self.j2env = Environment(loader=file_loader)


    def get_appointment_by_id(self, appt_id):
	response = requests.get(
	    "https://acuityscheduling.com/api/v1/appointments/" + appt_id,
	    auth=(self.USER_ID, self.API_KEY),
	)
	response_data = self.validate_response(response)
	for form in response_data['forms']:
	    for field in form['values']:
		if field['name'] == "Node Number":
		    node_number = field['value']
		elif field['name'] == "Address and Apartment #":
		    address = field['value']
		elif field['name'] == "Notes":
		    notes = field['value']

	appt_data = {
		'id': response_data['id'],
		'name': response_data['firstName'] + " " + response_data['lastName'],
		'phone': response_data['phone'],
		'datetime': response_data['datetime'],
		'type': response_data['type'],
		'duration': response_data['duration'],
		'node_number': node_number,
		'address': address,
		'notes': notes
		}

	return appt_data

    def get_appointment_types(self):
	response = requests.get("https://acuityscheduling.com/api/v1/appointment-types",
				auth=(self.USER_ID, self.API_KEY))
	response_data = self.validate_response(response)
	return [{'type_name': item['name'],
		'type_id': item['id'],
		'default_duration': item['duration'],
		'paddingBefore': item['paddingBefore'],
		'paddingAfter':item['paddingAfter']
		} for item in response_data]

    def validate_response(self, r):
	'''Takes a requests.response object. Returns the contents of the object in JSON format if the status_code is "200"
	if status_code is any other code it raises an exception detailing the errors as returned from the server.  '''

	if str(r.status_code) == '200':
	    return json.loads(r.content.decode())

	else:
	    m = self.build_error_message(r)
	    raise Exception(m)

    def build_error_message(self, r):
	return '\n' + datetime.datetime.now().isoformat() + ' \n Server responded with ' + r.status_code + '. \n error: ' + r.json()

    def parse_event(self, action, appt_id, channel_id):
	if action and appt_id and channel_id:
	    appointment = self.get_appointment_by_id(appt_id)
	    dateTime = dateutil.parser.parse(appointment['datetime'])

	    template = self.j2env.get_template('acuity_slack.j2')
	    #Add the varibles
	    output = template.render(appt_id=appt_id,
				    appt_type=appointment['type'],
				    node_number=appointment['node_number'],
				    name=appointment['name'],
				    date=dateTime.strftime("%A, %B %d, %Y"),
				    time=dateTime.strftime("%I:%M %p"),
				    address=appointment['address'],
				    phone=appointment['phone'],
				    notes=appointment['notes'],
				)
	    self.handle_event(appt_id, output, channel_id)

    def handle_event(self, appt_id, response, channel_id):
	print "Received webhook from acuity: " + appt_id + " in calendar"
	message = slack.post_to_channel(response, channel_id, False)
	pin = slack.pin_to_channel(message['channel'], message['ts'])

