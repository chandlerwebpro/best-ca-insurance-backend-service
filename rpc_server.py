from datetime import datetime
from datetime import timedelta
import json
from pprint import pprint
import requests

import mechanicalsoup

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

form_scraping_sessions = {}

def scraping_session_cleanup():
    global form_scraping_sessions

    now = datetime.now()
    expired = timedelta(hours=1)
    cleanup_list = []
    for session_key in form_scraping_sessions:
        if (now - form_scraping_sessions[session_key]['time']) > expired:
            cleanup_list.append(session_key)

    for session_key in cleanup_list:
        form_scraping_sessions.pop(session_key, None)

def step1(parameters):
    global form_scraping_sessions

    def get_counties(zipcode):
        url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetCounties'
        category = f"County,CA,{zipcode}"
        data = {"knownCategoryValues":"","category":category}
        r = requests.post(url, json=data)
        counties = json.loads(r.text)
        return counties['d']

    def get_cities(zipcode, county):
        url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetCities'
        knownCategoryValues = f"County,CA,{zipcode}:{county};"
        category = f"City,CA,{zipcode}"
        data = {"knownCategoryValues":knownCategoryValues,"category":category}
        r = requests.post(url, json=data)
        cities = json.loads(r.text)
        return cities['d']

    def get_regions(zipcode, city, county):
        url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetRegions'
        knownCategoryValues = f"County,CA,{zipcode}:{county};City,CA,{zipcode}:{city};"
        category = f"Region,CA,{zipcode}"
        data = {"knownCategoryValues":knownCategoryValues,"category":category}
        r = requests.post(url, json=data)
        regions = json.loads(r.text)
        return regions['d']

    print('form_scraping_sessions: ')
    pprint(form_scraping_sessions)

    browser = mechanicalsoup.StatefulBrowser() 
    form_scraping_sessions[parameters['form_session']] = {'browser_obj': browser, 'time': datetime.now()}
    scraping_session_cleanup()

    form_fields = parameters['form_fields']
    url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/welcome.aspx'
    browser.open(url)
    browser.launch_browser()
    browser.select_form('form')
    pprint(form_fields)
    browser['ctl00$CPH$WelcomeFirstNameEntry'] = form_fields['first_name']
    browser['ctl00$CPH$WelcomeLastNameEntry'] = form_fields['last_name']
    browser['ctl00$CPH$WelcomeEmailAddressEntry'] = form_fields['email']
    browser['ctl00$CPH$PhoneEntry'] = form_fields['contact_phone']
    browser['ctl00$CPH$PhoneTypeEntry'] = form_fields['phone_type']
    browser['ctl00$CPH$ZipCodeEntry'] = form_fields['zip_code']
    browser.submit_selected()
    browser.launch_browser()
    # need to add check to see that remote form as moved to next page
    current_url = browser.get_url() # check the url to determine where we are

    response = {}
    counties = get_counties(form_fields['zip_code'])
    for row in counties:
        if row['isDefaultValue']:
            county = row['value']
            break
    else:
        county = counties[0]['value']

    cities = get_cities(form_fields['zip_code'], county)
    for row in cities:
        if row['isDefaultValue']:
            city = row['value']
            break
    else:
        city = counties[0]['value']

    regions = get_regions(form_fields['zip_code'], city, county)

    response['counties'] = counties
    response['cities'] = cities
    response['regions'] = regions
    return json.dumps(response)

def step2(parameters):
    if parameters['form_session'] in form_scraping_sessions:
        scraping_session_cleanup()
        browser = form_scraping_sessions[parameters['form_session']]['browser_obj']
    else:
        pass # error lost remote form state

    browser.select_form('form')
    browser['ctl00$CPH$InsuredAddress1Entry'] = form_fields['address1']
    browser['ctl00$CPH$InsuredAddress2Entry'] = form_fields['address2']

def on_request(ch, method, props, body):
    global form_scraping_sessions
    parameters = json.loads(body)
    pprint(parameters)
    if parameters['form_step'] == 'step1':
        response = step1(parameters)
    elif parameters['form_step'] == 'step2':
        response = step2(parameters)

    else:
        response = {'error': 'no such form_step'}

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_queue')

print(" [x] Awaiting RPC requests")
channel.start_consuming()
