# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_onionsearchengine
# Purpose:      Searches the Tor search engine onionsearchengine.com for content 
#               related to the domain in question.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     27/10/2018
# Copyright:   (c) Steve Micallef 2018
# Licence:     GPL
# -------------------------------------------------------------------------------

try:
    import re2 as re
except ImportError as e:
    import re

import urllib.request, urllib.parse, urllib.error
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_onionsearchengine(SpiderFootPlugin):
    """Onionsearchengine.com:Footprint,Investigate:Search Engines::Search Tor onionsearchengine.com for mentions of the target domain."""

    # Default options
    opts = {
        'timeout': 10,
        'max_pages': 20,
        'fetchlinks': True,
        'blacklist': [ '.*://relate.*' ]
    }

    # Option descriptions
    optdescs = {
        'timeout': "Query timeout, in seconds.",
        'max_pages': "Maximum number of pages of results to fetch.",
        'fetchlinks': "Fetch the darknet pages (via TOR, if enabled) to verify they mention your target.",
        'blacklist': "Exclude results from sites matching these patterns."
    }

    results = None

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ["DOMAIN_NAME", "HUMAN_NAME", "EMAILADDR"]

    # What events this module produces
    # This is to support the end user in selecting modules based on events
    # produced.
    def producedEvents(self):
        return ["DARKNET_MENTION_URL", "DARKNET_MENTION_CONTENT", "SEARCH_ENGINE_WEB_CONTENT"]

    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        if eventData in self.results:
            self.sf.debug("Already did a search for " + eventData + ", skipping.")
            return None

        self.results[eventData] = True

        keepGoing = True
        page = 1
        while keepGoing and page <= int(self.opts['max_pages']):
            # Check if we've been asked to stop
            if self.checkForStop():
                return None

            params = {
                'search': '"' + eventData.encode('raw_unicode_escape') + '"',
                'submit': 'Search',
                'page': str(page)
            }

            # Sites hosted on the domain
            data = self.sf.fetchUrl('https://onionsearchengine.com/search.php?' + urllib.parse.urlencode(params),
                                    useragent=self.opts['_useragent'], 
                                    timeout=self.opts['timeout'])

            if data is None or not data.get('content'):
                self.sf.info("No results returned from onionsearchengine.com.")
                return None

            page += 1

            if "url.php?u=" not in data['content']:
                # Work around some kind of bug in the site
                if "you didn't submit a keyword" in data['content']:
                    continue
                return None

            if "forward >" not in data['content']:
                keepGoing = False

            # Submit the google results for analysis
            evt = SpiderFootEvent("SEARCH_ENGINE_WEB_CONTENT", data['content'],
                                  self.__name__, event)
            self.notifyListeners(evt)

            links = re.findall("url\.php\?u=(.[^\"\']+)[\"\']", 
                               data['content'], re.IGNORECASE | re.DOTALL)

            for link in links:
                if self.checkForStop():
                    return None

                if link in self.results:
                    continue

                self.results[link] = True

                blacklist = False
                for r in self.opts['blacklist']:
                    if re.match(r, link, re.IGNORECASE):
                        self.sf.debug("Skipping " + link + " as it matches blacklist " + r)
                        blacklist = True
                if blacklist:
                    continue

                self.sf.debug("Found a darknet mention: " + link)

                if not self.sf.urlFQDN(link).endswith(".onion"):
                    continue

                if not self.opts['fetchlinks']:
                    evt = SpiderFootEvent("DARKNET_MENTION_URL", link, self.__name__, event)
                    self.notifyListeners(evt)
                    continue

                res = self.sf.fetchUrl(link,
                                       timeout=self.opts['_fetchtimeout'],
                                       useragent=self.opts['_useragent'])

                if res['content'] is None:
                    self.sf.debug("Ignoring " + link + " as no data returned")
                    continue

                if eventData not in res['content']:
                    self.sf.debug("Ignoring " + link + " as no mention of " + eventData)
                    continue

                evt = SpiderFootEvent("DARKNET_MENTION_URL", link, self.__name__, event)
                self.notifyListeners(evt)

                try:
                    startIndex = res['content'].index(eventData) - 120
                    endIndex = startIndex + len(eventData) + 240
                except BaseException as e:
                    self.sf.debug('String "' + eventData + '" not found in content.')
                    continue

                data = res['content'][startIndex:endIndex]
                evt = SpiderFootEvent("DARKNET_MENTION_CONTENT", "..." + data + "...",
                                      self.__name__, evt)
                self.notifyListeners(evt)

# End of sfp_onionsearchengine class
