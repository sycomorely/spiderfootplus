# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_snov
# Purpose:      Spiderfoot plugin to search Snov.IO API for emails 
#               associated to target domain
#
# Author:      Krishnasis Mandal <krishnasis@hotmail.com>
#
# Created:     16/05/2020
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent
import urllib.request, urllib.parse, urllib.error
import json

class sfp_snov(SpiderFootPlugin):
    """Snov:Footprint,Investigate,Passive:Search Engines:apikey:Gather available email IDs from identified domains"""

    opts = {
        'api_key_client_id': '',
        'api_key_client_secret': ''
    }

    # Option descriptions. Delete any options not applicable to this module.
    optdescs = {
        'api_key_client_id': "Client ID for snov.io API",
        'api_key_client_secret': "Client Secret for snov.io API"
    }

    results = None
    errorState = False  

    # More than 100 per response is not supported by Snov API
    limit = 100

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]
        

    # What events is this module interested in for input
    # For a list of all events, check sfdb.py.
    def watchedEvents(self):
        return ["DOMAIN_NAME", "INTERNET_NAME"]

    # What events this module produces
    def producedEvents(self):
        return ["EMAILADDR"]
    
    # Get Authentication token from Snov.IO API
    def queryAccessToken(self):
        params = {
            'grant_type': "client_credentials",
            'client_id': self.opts['api_key_client_id'],
            'client_secret': self.opts['api_key_client_secret']
        }

        headers = {
            'Accept': "application/json",
        }
        
        res = self.sf.fetchUrl(
            'https://api.snov.io/v1/oauth/access_token?' + urllib.parse.urlencode(params),
            headers=headers,
            timeout=15,
            useragent=self.opts['_useragent']
        )

        if not res['code'] == '200':
            self.sf.error("No access token received from snov.io for the provided Client ID and/or Client Secret", False)
            self.errorState = True 
            return None
        try:
            # Extract access token from response
            content = res.get('content')
            accessToken = json.loads(content).get('access_token')
            
            if accessToken is None:
                self.sf.error("No access token received from snov.io for the provided Client ID and/or Client Secret", False)
                return None

            return str(accessToken)
        except Exception: 
            self.sf.error("No access token received from snov.io for the provided Client ID and/or Client Secret", False)
            self.errorState = True
            return None
        
    # Fetch email addresses related to target domain
    def queryDomainName(self, qry, accessToken, currentOffset):
        params = {
            'domain': qry.encode('raw_unicode_escape').decode("ascii", errors='replace'),
            'access_token': accessToken,
            'type': "all",
            'limit': str(self.limit),
            'offset': str(currentOffset)
        }

        headers = {
            'Accept' : "application/json",
        }

        res = self.sf.fetchUrl(
            'https://api.snov.io/v1/get-domain-emails-with-info',
            postData=params,
            headers=headers,
            timeout=15,
            useragent=self.opts['_useragent']
        )
        if not res['code'] == '200':
            self.sf.debug("Could not fetch email addresses")
            return None

        return res.get('content')

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data
        
        if self.errorState:
            return None

        self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

        # Always check if the API key is set and complain if it isn't, then set
        # self.errorState to avoid this being a continual complaint during the scan.
        if self.opts['api_key_client_id'] == "" or self.opts['api_key_client_secret'] == "":
            self.sf.error("You enabled sfp_snov but did not set a Client ID and/or Client Secret", False)
            self.errorState = True
            return None

        # Don't look up stuff twice
        if eventData in self.results:
            self.sf.debug("Skipping " + eventData + " as already mapped.")
            return None
        else:
            self.results[eventData] = True

        # Get access token from Snov IO API
        accessToken = self.queryAccessToken()
        if accessToken is None or accessToken == '':
            self.sf.error("No access token received from snov.io for the provided Client ID and/or Client Secret", False)
            self.errorState = True
            return None

        currentOffset = 0
        nextPageHasData = True

        while nextPageHasData:
            if self.checkForStop():
                return None

            data = self.queryDomainName(eventData, accessToken, currentOffset)
            if data is None:
                self.sf.debug("No email address found for target domain")
                break

            try:
                data = json.loads(data)
            except:
                self.sf.debug("No email address found for target domain")
                break
            
            evt = SpiderFootEvent("RAW_RIR_DATA", str(data), self.__name__, event)
            self.notifyListeners(evt)

            records = data.get('emails')
            
            if records:
                for record in records:
                    if record:
                        email = record.get('email')
                        if email:
                            if email in self.results:
                                continue
                            self.results[email] = True

                            evt = SpiderFootEvent("EMAILADDR", str(email), self.__name__, event)
                            self.notifyListeners(evt)

            # Determine whether the next offset can have data or not 
            if len(records) < self.limit:
                nextPageHasData = False
            currentOffset += self.limit

        return None
# End of sfp_snov class
