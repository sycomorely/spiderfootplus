# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_ipstack
# Purpose:      SpiderFoot plug-in to identify the Geo-location of IP addresses
#               identified by other modules using ipstack.com.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     20/08/2018
# Copyright:   (c) Steve Micallef 2018
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent


class sfp_ipstack(SpiderFootPlugin):
    """ipstack:Footprint,Investigate,Passive:Real World:apikey:Identifies the physical location of IP addresses identified using ipstack.com."""

    meta = {
        'name': "ipstack",
        'summary': "Identifies the physical location of IP addresses identified using ipstack.com.",
        'flags': [ "apikey" ],
        'useCases': [ "Footprint", "Investigate", "Passive" ],
        'categories': [ "Real World" ],
        'dataSource': {
            'website': "https://ipstack.com/",
            'model': "FREE_AUTH_LIMITED",
            'references': [
                "https://ipstack.com/documentation",
                "https://ipstack.com/faq"
            ],
            'apiKeyInstructions': [
                "Visit ipstack.com/product",
                "Click on 'Get Free API Key'",
                "Click on 'Dashboard'",
                "The API key is listed under 'Your API Access Key'"
            ],
            'favIcon': "https://ipstack.com/ipstack_images/ipstack_logo.svg",
            'logo': "https://ipstack.com/ipstack_images/ipstack_logo.svg",
            'description': "Locate and identify website visitors by IP address.\n"
                                "ipstack offers one of the leading IP to geolocation APIS "
                                "and global IP database services worldwide.",
        }
    }

    # Default options
    opts = {
        "api_key": ""
    }
    optdescs = {
        "api_key": "Ipstack.com API key."
    }
    results = None
    errorState = False

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()
        self.errorState = False

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ['IP_ADDRESS']

    # What events this module produces
    # This is to support the end user in selecting modules based on events
    # produced.
    def producedEvents(self):
        return ["GEOINFO"]

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        self.sf.debug("Received event, %s, from %s" % (eventName, srcModuleName))

        if self.errorState:
            return None

        if self.opts['api_key'] == "":
            self.sf.error("You enabled sfp_ipstack but did not set an API key!", False)
            self.errorState = True
            return None

        # Don't look up stuff twice
        if eventData in self.results:
            self.sf.debug("Skipping " + eventData + " as already mapped.")
            return None
        else:
            self.results[eventData] = True

        res = self.sf.fetchUrl("http://api.ipstack.com/" + eventData + "?access_key="  + self.opts['api_key'],
                               timeout=self.opts['_fetchtimeout'], useragent=self.opts['_useragent'])
        if res['content'] is None:
            self.sf.info("No GeoIP info found for " + eventData)

        try:
            hostip = json.loads(res['content'])
            if 'success' in hostip and hostip['success'] == False:
                self.sf.error("Invalid ipstack.com API key or usage limits exceeded.", False)
                self.errorState = True
                return None
        except Exception as e:
            self.sf.debug("Error processing JSON response.")
            return None

        if hostip.get('country_name', None) != None:
            self.sf.info("Found GeoIP for " + eventData + ": " + hostip['country_name'])
            countrycity = hostip['country_name']

            evt = SpiderFootEvent("GEOINFO", countrycity, self.__name__, event)
            self.notifyListeners(evt)

        return None

# End of sfp_ipstack class
