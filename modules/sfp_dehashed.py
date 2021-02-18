# -------------------------------------------------------------------------------
# Name:        sfp_dehashed
# Purpose:     Gather breach data from Dehashed API.
#
# Author:      <krishnasis@hotmail.com>
#
# Created:     16-01-2021
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
import time
import base64
from spiderfoot import SpiderFootEvent, SpiderFootPlugin


class sfp_dehashed(SpiderFootPlugin):

    meta = {
        'name': "Dehashed",
        'summary': "Gather breach data from Dehashed API.",
        'flags': ["apikey"],
        'useCases': ["Footprint", "Investigate", "Passive"],
        'categories': ["Leaks, Dumps and Breaches"],
        'dataSource': {
            'website': "https://www.dehashed.com/",
            'model': "COMMERCIAL_ONLY",
            'references': [
                "https://www.dehashed.com/docs"
            ],
            'favIcon': "https://www.dehashed.com/assets/img/favicon.ico",
            'logo': "https://www.dehashed.com/assets/img/logo.png",
            'description': "Have you been compromised? "
            "DeHashed provides free deep-web scans and protection against credential leaks. "
            "A modern personal asset search engine created for "
            "security analysts, journalists, security companies, "
            "and everyday people to help secure accounts and provide insight on compromised assets. "
            "Free breach alerts & breach notifications.",
        }
    }

    # Default options
    opts = {
        'api_key_username': '',
        'api_key': '',
        'per_page': 10000,
        'max_pages': 2,
        'pause': 1
    }

    # Option descriptions
    optdescs = {
        'api_key_username': 'Dehashed username.',
        'api_key': 'Dehashed API key.',
        'per_page': 'Maximum number of results per page.(Max: 10000)',
        'max_pages': 'Maximum number of pages to fetch(Max: 10 pages)',
        'pause': 'Number of seconds to wait between each API call.'
    }

    results = None
    errorState = False

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return [
            "DOMAIN_NAME",
            "EMAILADDR"
        ]

    # What events this module produces
    def producedEvents(self):
        return [
            'EMAILADDR',
            'EMAILADDR_COMPROMISED',
            'PASSWORD_COMPROMISED',
            'HASH_COMPROMISED',
            'RAW_RIR_DATA'
        ]

    # Query Dehashed
    def query(self, event, per_page, start):
        if event.eventType == "EMAILADDR":
            queryString = f"https://api.dehashed.com/search?query=email:\"{event.data}\"&page={start}&size={self.opts['per_page']}"
        if event.eventType == "DOMAIN_NAME":
            queryString = f"https://api.dehashed.com/search?query=email:\"@{event.data}\"&page={start}&size={self.opts['per_page']}"

        token = (base64.b64encode(self.opts['api_key_username'].encode('utf8') + ":".encode('utf-8') + self.opts['api_key'].encode('utf-8'))).decode('utf-8')
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Basic {token}'
        }

        res = self.sf.fetchUrl(queryString,
                               headers=headers,
                               timeout=15,
                               useragent=self.opts['_useragent'],
                               verify=True)

        time.sleep(self.opts['pause'])

        if res['code'] == "400":
            self.sf.error("Too many requests were performed in a small amount of time. Please wait a bit before querying the API.")
            time.sleep(5)
            res = self.sf.fetchUrl(queryString, headers=headers, timeout=15, useragent=self.opts['_useragent'], verify=True)

        if res['code'] == "401":
            self.sf.error("Invalid API credentials")
            self.errorState = True
            return None

        if res['code'] != "200":
            self.sf.error("Unable to fetch data from Dehashed.")
            self.errorState = True
            return None

        if res['content'] is None:
            self.sf.debug('No response from Dehashed')
            return None

        try:
            return json.loads(res['content'])
        except Exception as e:
            self.sf.debug(f"Error processing JSON response: {e}")
            return None

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        if srcModuleName == self.__name__:
            return None

        if eventData in self.results:
            return None

        if self.errorState:
            return None

        self.results[eventData] = True

        self.sf.debug(f"Received event, {eventName}, from {srcModuleName}")

        if self.opts['api_key'] == "" or self.opts['api_key_username'] == "":
            self.sf.error("You enabled sfp_dehashed but did not set an API key/API Key Username!")
            self.errorState = True
            return

        currentPage = 1
        maxPages = self.opts['max_pages']
        perPage = self.opts['per_page']

        while currentPage <= maxPages:
            if self.checkForStop():
                return None

            if self.errorState:
                break

            data = self.query(event, perPage, currentPage)

            if not data:
                return None

            breachResults = set()
            emailResults = set()

            for row in data.get('entries'):
                email = row.get('email')
                password = row.get('password')
                passwordHash = row.get('hashed_password')
                leakSource = row.get('database_name', 'Unknown')

                if f"{email} [{leakSource}]" in breachResults:
                    continue

                breachResults.add(f"{email} [{leakSource}]")

                if eventName == "EMAILADDR":
                    if email == eventData:
                        evt = SpiderFootEvent('EMAILADDR_COMPROMISED', f"{email} [{leakSource}]", self.__name__, event)
                        self.notifyListeners(evt)

                        if password:
                            evt = SpiderFootEvent('PASSWORD_COMPROMISED', f"{email}:{password} [{leakSource}]", self.__name__, event)
                            self.notifyListeners(evt)

                        if passwordHash:
                            evt = SpiderFootEvent('HASH_COMPROMISED', f"{email}:{passwordHash} [{leakSource}]", self.__name__, event)
                            self.notifyListeners(evt)

                        evt = SpiderFootEvent('RAW_RIR_DATA', str(row), self.__name__, event)
                        self.notifyListeners(evt)

                if eventName == "DOMAIN_NAME":
                    pevent = SpiderFootEvent("EMAILADDR", email, self.__name__, event)
                    if email not in emailResults:
                        self.notifyListeners(pevent)
                        emailResults.add(email)

                    evt = SpiderFootEvent('EMAILADDR_COMPROMISED', f"{email} [{leakSource}]", self.__name__, pevent)
                    self.notifyListeners(evt)

                    if password:
                        evt = SpiderFootEvent('PASSWORD_COMPROMISED', f"{email}:{password} [{leakSource}]", self.__name__, pevent)
                        self.notifyListeners(evt)

                    if passwordHash:
                        evt = SpiderFootEvent('HASH_COMPROMISED', f"{email}:{passwordHash} [{leakSource}]", self.__name__, pevent)
                        self.notifyListeners(evt)

                    evt = SpiderFootEvent('RAW_RIR_DATA', str(row), self.__name__, pevent)
                    self.notifyListeners(evt)

            currentPage += 1

            if data.get('total') < self.opts['per_page']:
                return None

# End of sfp_dehashed class
