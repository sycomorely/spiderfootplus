#-------------------------------------------------------------------------------
# Name:         sfp_psbdmp
# Purpose:      Query psbdmp.cc for potentially hacked e-mail addresses.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     21/11/2016
# Copyright:   (c) Steve Micallef
# Licence:     GPL
#-------------------------------------------------------------------------------

import json
import re

from spiderfoot import SpiderFootEvent, SpiderFootPlugin


class sfp_psbdmp(SpiderFootPlugin):

    meta = {
        'name': "Psbdmp",
        'summary': "Check psbdmp.cc (PasteBin Dump) for potentially hacked e-mails and domains.",
        'flags': [""],
        'useCases': ["Footprint", "Investigate", "Passive"],
        'categories': ["Leaks, Dumps and Breaches"],
        'dataSource': {
            'website': "https://psbdmp.cc/",
            'model': "FREE_NOAUTH_UNLIMITED",
            'references': [
                "https://psbdmp.cc/"
            ],
            'favIcon': "",
            'logo': "",
            'description': "Search dump(s) by some word.\n"
                                "Search dump(s) by email.\n"
                                "Search dump(s) by domain.\n"
                                "Search dump(s) from specific date.",
        }
    }

    # Default options
    opts = {
    }

    # Option descriptions
    optdescs = {
    }

    # Be sure to completely clear any class variables in setup()
    # or you run the risk of data persisting between scan runs.

    results = None

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        # Clear / reset any other class member variables here
        # or you risk them persisting between threads.

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        ret = ["EMAILADDR", "DOMAIN_NAME", "INTERNET_NAME"]

        return ret

    # What events this module produces
    def producedEvents(self):
        ret = ["LEAKSITE_URL", "LEAKSITE_CONTENT"]

        return ret

    def query(self, qry):
        ret = None

        if "@" in qry:
            url = "https://psbdmp.cc/api/search/email/" + qry
        else:
            url = "https://psbdmp.cc/api/search/domain/" + qry

        res = self.sf.fetchUrl(url, timeout=15, useragent="SpiderFoot")

        if res['code'] == "403" or res['content'] is None:
            self.sf.info("Unable to fetch data from psbdmp.cc right now.")
            return None

        try:
            ret = json.loads(res['content'])
        except Exception as e:
            self.sf.error(f"Error processing JSON response from psbdmp.cc: {e}", False)
            return None

        ids = list()
        if 'count' not in ret:
            return None

        if ret['count'] <= 0:
            return None

        for d in ret['data']:
            ids.append("https://pastebin.com/" + d['id'])

        return ids

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        self.sf.debug(f"Received event, {eventName}, from {srcModuleName}")

        # Don't look up stuff twice
        if eventData in self.results:
            self.sf.debug(f"Skipping {eventData}, already checked.")
            return None
        else:
            self.results[eventData] = True

        data = self.query(eventData)
        if data is None:
            return None

        for n in data:
            e = SpiderFootEvent("LEAKSITE_URL", n, self.__name__, event)
            self.notifyListeners(e)

            res = self.sf.fetchUrl(n, timeout=self.opts['_fetchtimeout'],
                                   useragent=self.opts['_useragent'])

            if res['content'] is None:
                self.sf.debug("Ignoring " + n + " as no data returned")
                continue

            # Sometimes pastes search results false positives
            if re.search(r"[^a-zA-Z\-\_0-9]" + re.escape(eventData) +
                         r"[^a-zA-Z\-\_0-9]", res['content'], re.IGNORECASE) is None:
                continue

            try:
                startIndex = res['content'].index(eventData)
            except BaseException:
                self.sf.debug("String not found in pastes content.")
                continue

            evt = SpiderFootEvent("LEAKSITE_CONTENT", res['content'], self.__name__, e)
            self.notifyListeners(evt)

# End of sfp_psbdmp class
