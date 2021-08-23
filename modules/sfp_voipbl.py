# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        sfp_voipbl
# Purpose:     Check if an IP address or netblock is malicious according to VoIPBL
#              VoIP Blacklist.
#
# Author:       steve@binarypool.com
#
# Created:     14/12/2013
# Copyright:   (c) Steve Micallef, 2013
# Licence:     GPL
# -------------------------------------------------------------------------------

from netaddr import IPAddress, IPNetwork
from spiderfoot import SpiderFootEvent, SpiderFootPlugin


class sfp_voipbl(SpiderFootPlugin):

    meta = {
        'name': "VoIP Blacklist (VoIPBL)",
        'summary': "Check if an IP address or netblock is malicious according to VoIP Blacklist (VoIPBL).",
        'flags': [],
        'useCases': ["Investigate", "Passive"],
        'categories': ["Reputation Systems"],
        'dataSource': {
            'website': "https://voipbl.org/",
            'model': "FREE_NOAUTH_UNLIMITED",
            'references': [
                "https://voipbl.org/#install",
                "https://voipbl.org/#advanced"
            ],
            'favIcon': "",
            'logo': "https://voipbl.org/images/scopserv.png",
            'description': "VoIPBL is a distributed VoIP blacklist that is aimed to protect against\n"
            "VoIP Fraud and minimizing abuse for network that have publicly accessible PBXs."
        }
    }

    # Default options
    opts = {
        'checkaffiliates': True,
        'cacheperiod': 18,
        'checknetblocks': True,
        'checksubnets': True
    }

    # Option descriptions
    optdescs = {
        'checkaffiliates': "Apply checks to affiliates?",
        'cacheperiod': "Hours to cache list data before re-fetching.",
        'checknetblocks': "Report if any malicious IPs are found within owned netblocks?",
        'checksubnets': "Check if any malicious IPs are found within the same subnet of the target?"
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
        return [
            "IP_ADDRESS",
            "AFFILIATE_IPADDR",
            "NETBLOCK_MEMBER",
            "NETBLOCK_OWNER"
        ]

    # What events this module produces
    def producedEvents(self):
        return [
            "MALICIOUS_IPADDR",
            "MALICIOUS_AFFILIATE_IPADDR",
            "MALICIOUS_SUBNET",
            "MALICIOUS_NETBLOCK"
        ]

    def queryBlacklist(self, target, targetType):
        blacklist = self.retrieveBlacklist()

        if targetType == "ip":
            if target in blacklist:
                self.sf.debug(f"IP address {target} found in VoIP Blacklist (VoIPBL).")
                return True
        elif targetType == "netblock":
            netblock = IPNetwork(target)
            for ip in blacklist:
                if IPAddress(ip) in netblock:
                    self.sf.debug(f"IP address {ip} found within netblock/subnet {target} in VoIP Blacklist (VoIPBL).")
                    return True

        return False

    def retrieveBlacklist(self):
        blacklist = self.sf.cacheGet('voipbl', 24)

        if blacklist is not None:
            return self.parseBlacklist(blacklist)

        res = self.sf.fetchUrl(
            "https://voipbl.org/update",
            timeout=self.opts['_fetchtimeout'],
            useragent=self.opts['_useragent'],
        )

        if res['code'] != "200":
            self.sf.error(f"Unexpected HTTP response code {res['code']} from VoIP Blacklist (VoIPBL).")
            self.errorState = True
            return

        if res['content'] is None:
            self.sf.error("Received no content from VoIP Blacklist (VoIPBL)")
            self.errorState = True
            return

        self.sf.cachePut("voipbl", res['content'])

        return self.parseBlacklist(res['content'])

    def parseBlacklist(self, blacklist):
        """Parse plaintext blacklist

        Args:
            blacklist (str): plaintext blacklist from VoIP Blacklist (VoIPBL)

        Returns:
            list: list of blacklisted IP addresses
        """
        ips = list()

        if not blacklist:
            return ips

        for cidr in blacklist.split('\n'):
            cidr = cidr.strip()
            if not cidr:
                continue
            if cidr.startswith('#'):
                continue

            try:
                for ip in IPNetwork(cidr):
                    ips.append(str(ip))
            except Exception:
                continue

        return ips

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        self.sf.debug(f"Received event, {eventName}, from {srcModuleName}")

        if eventData in self.results:
            self.sf.debug(f"Skipping {eventData}, already checked.")
            return

        if self.errorState:
            return

        self.results[eventData] = True

        if eventName == 'IP_ADDRESS':
            targetType = 'ip'
            evtType = 'MALICIOUS_IPADDR'
        elif eventName == 'AFFILIATE_IPADDR':
            if not self.opts.get('checkaffiliates', False):
                return
            targetType = 'ip'
            evtType = 'MALICIOUS_AFFILIATE_IPADDR'
        elif eventName == 'NETBLOCK_OWNER':
            if not self.opts.get('checknetblocks', False):
                return
            targetType = 'netblock'
            evtType = 'MALICIOUS_NETBLOCK'
        elif eventName == 'NETBLOCK_MEMBER':
            if not self.opts.get('checksubnets', False):
                return
            targetType = 'netblock'
            evtType = 'MALICIOUS_SUBNET'
        else:
            return

        self.sf.debug(f"Checking maliciousness of {eventData} ({eventName}) with VoIP Blacklist (VoIPBL)")

        if self.queryBlacklist(eventData, targetType):
            url = "https://voipbl.org/update"
            text = f"VoIP Blacklist (VoIPBL) [{eventData}]\n<SFURL>{url}</SFURL>"
            evt = SpiderFootEvent(evtType, text, self.__name__, event)
            self.notifyListeners(evt)

# End of sfp_voipbl class
