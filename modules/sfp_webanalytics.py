# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_webanalytics
# Purpose:      SpiderFoot plug-in for scanning retrieved content by other
#               modules (such as sfp_spider) and identifying web analytics IDs.
#
# Author:      Brendan Coles <bcoles@gmail.com>
#
# Created:     2018-10-28
# Copyright:   (c) Brendan Coles 2018
# Licence:     GPL
# -------------------------------------------------------------------------------

import re
from hashlib import sha256
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_webanalytics(SpiderFootPlugin):
    """Web Analytics:Footprint,Investigate:Content Analysis::Identify web analytics IDs in scraped webpages."""

    opts = {}
    optdescs = {}

    results = dict()

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = dict()

        for opt in userOpts.keys():
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ["TARGET_WEB_CONTENT"]

    # What events this module produces
    def producedEvents(self):
        return ["WEB_ANALYTICS_ID"]

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data
        sourceData = self.sf.hashstring(eventData)

        if sourceData in self.results:
            return None

        self.results[sourceData] = True

        self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

        # Google Analytics
        matches = re.findall(r"\bua\-\d{4,10}\-\d{1,4}\b", eventData, re.IGNORECASE)
        for m in matches:
            if m.lower().startswith('ua-000000-'):
                continue
            if m.lower().startswith('ua-123456-'):
                continue
            if m.lower().startswith('ua-123456789'):
                continue

            self.sf.debug("Google Analytics match: " + m)
            evt = SpiderFootEvent("WEB_ANALYTICS_ID", "Google Analytics: " + m, self.__name__, event)
            self.notifyListeners(evt)

        # Google AdSense
        matches = re.findall(r"\b(pub-\d{10,20})\b", eventData, re.IGNORECASE)
        for m in matches:
            if m.lower().startswith('pub-123456789'):
                continue

            self.sf.debug("Google AdSense match: " + m)
            evt = SpiderFootEvent("WEB_ANALYTICS_ID", "Google AdSense: " + m, self.__name__, event)
            self.notifyListeners(evt)

        return None

# End of sfp_webanalytics class
