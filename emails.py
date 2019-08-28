import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _create_message(flight_data):

    formatted_message = MIMEMultipart('alternative')
    formatted_message['subject'] = 'Cebu Pacific: {0} to {1}'.format(flight_data['origin'], flight_data['destination'])

    text = _format_data_into_plaintext(flight_data)
    html = _format_data_into_html(flight_data)

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    formatted_message.attach(part1)
    formatted_message.attach(part2)

    return formatted_message

def _format_data_into_plaintext(flight_data):

    list_of_flight_data = []

    for month in flight_data['flights']:

        list_of_flight_data += flight_data['flights'][month]
        
    text = '\n'.join(list_of_flight_data)
    return "Origin: {}, Destination: {} \n".format(flight_data['origin'], flight_data['destination']) + text
    

def _format_data_into_html(flight_data):

    flight_data_per_month = []

    for month in flight_data['flights']:

        flights = '<br>'.join(flight_data['flights'][month])
        flight_data_per_month.append('<div class="flights">{data}</div>'.format(data=flights))

    html = """\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>Cebu Pacific bois</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Foco', 'Montserrat', 'sans-serif';
                background-color: #EBEBEB;
            }}
            header {{
                background-color: #FEE020;
            }}
            header h1 {{
                color: #3471B9;
            }}
            .flights {{
                column-count: 3;
                column-fill: auto;
                margin: 2em 0;
            }}
            br {{
                line-height: 2em;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Cebu Pacific flights: {origin} to {destination}</h1>
        </header>
        {div_flights}
    </body>
    </html>""".format(origin=flight_data['origin'], destination=flight_data['destination'], div_flights=''.join(flight_data_per_month))

    return html


# Create a secure SSL context
def _initialize_email_server(config):

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(config['smtp_server'], config['port'], context=context)
    server.login(config['sender_email'], config['password'])

    return server


def send_email(config, flight_data):

    server = _initialize_email_server(config)
    formatted_message = _create_message(flight_data)

    for email in config['receiver_emails']:
        server.sendmail(config['sender_email'], email, formatted_message.as_string())