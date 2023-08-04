import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml
import requests
import mysql.connector
import os

def check_services(services_list):
    failure_list = []
    for services_dict in services_list:
        if services_dict['service_type'] == 'Webservice':
            try:
                response = requests.get(services_dict['service_url'])
                json_data = response.json()
                if 'status' in json_data[0]:
                    if json_data[0]['status'] != 'Working':
                        failure_list.append(services_dict)
            except:
                failure_list.append(services_dict)
        if services_dict['service_type'] == 'HttpCode':
            try:
                response = requests.get(services_dict['service_url'])
                if response.status_code != 200:
                    failure_list.append(services_dict)
            except:
                failure_list.append(services_dict)
        if services_dict['service_type'] == 'Database':
            try:
                db = mysql.connector.connect(
                host = services_dict['service_url'],
                user = services_dict['db_user'],
                password = services_dict['db_password'],
                database = services_dict['db_name']
                )
                db.time_zone = '+00:00'
                db.close()
            except:
                failure_list.append(services_dict)

    return failure_list

def send_mail_notification(mail_content, subject):
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject
    message.attach(MIMEText(mail_content, 'html'))
    session = smtplib.SMTP(smtp_host, smtp_port)
    session.starttls()
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()

def create_html_payload(services_list):
    payload = '''<!DOCTYPE html>
<html>
<head>
<style>
table, th, td {
  border: 1px solid black;
}
</style>
</head>
<body>
<h2>Serwery offline</h2>
<table style="width:100%">

  <tr><th>Typ</th><th>Nazwa</th><th>URL</th></tr>'''
    for service in services_list:
        payload += "<tr>"
        payload += "<td>" + service['service_type'] + "</td>"
        payload += "<td>" + service['service_name'] + "</td>"
        payload += "<td>" + service['service_url'] + "</td>"
        payload += "</tr>"
    payload += "</table></body></html>"
    return payload
with open((os.path.join(os.path.abspath(os.path.dirname(__file__)),'./config.yaml'))) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

sender_address = config['sender_address']
sender_pass = config['sender_pass']
receiver_address = config['receiver_address']
default_subject = config['default_subject']
smtp_host = config['smtp_host']
smtp_port = config['smtp_port']

services_list = config['services']

services_failed = check_services(services_list)
if len(services_failed) > 0:
    mail_content = create_html_payload(services_failed)
    send_mail_notification(mail_content, default_subject)
    