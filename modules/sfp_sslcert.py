# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_sslcert
# Purpose:      Gather information about SSL certificates behind HTTPS sites.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     23/08/2013
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

import time
import urlparse
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent


class sfp_sslcert(SpiderFootPlugin):
    """SSL Certificates:Footprint,Investigate:Crawling and Scanning::Gather information about SSL certificates used by the target's HTTPS sites."""

    # Default options
    opts = {
        "tryhttp": True,
        'verify': True,
        "ssltimeout": 10,
        "certexpiringdays": 30
    }

    # Option descriptions
    optdescs = {
        "tryhttp": "Also try to HTTPS-connect to HTTP sites and hostnames.",
        'verify': "Verify certificate subject alternative names resolve.",
        "ssltimeout": "Seconds before giving up trying to HTTPS connect.",
        "certexpiringdays": "Number of days in the future a certificate expires to consider it as expiring."
    }

    # Be sure to completely clear any class variables in setup()
    # or you run the risk of data persisting between scan runs.

    results = None

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        # Clear / reset any other class member variables here
        # or you risk them persisting between threads.

        for opt in userOpts.keys():
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    # * = be notified about all events.
    def watchedEvents(self):
        return ["INTERNET_NAME", "LINKED_URL_INTERNAL", "IP_ADDRESS"]

    # What events this module produces
    # This is to support the end user in selecting modules based on events
    # produced.
    def producedEvents(self):
        return ['TCP_PORT_OPEN', 'INTERNET_NAME', 'INTERNET_NAME_UNRESOLVED',
                'AFFILIATE_DOMAIN', 'AFFILIATE_DOMAIN_UNRESOLVED',
                "SSL_CERTIFICATE_ISSUED", "SSL_CERTIFICATE_ISSUER",
                "SSL_CERTIFICATE_MISMATCH", "SSL_CERTIFICATE_EXPIRED",
                "SSL_CERTIFICATE_EXPIRING", "SSL_CERTIFICATE_RAW"]

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

        if eventName == "LINKED_URL_INTERNAL":
            if not eventData.lower().startswith("https://") and not self.opts['tryhttp']:
                return None

            # Handle URLs containing port numbers
            u = urlparse.urlparse(eventData)
            port = 443
            if url.port:
                port = url.port
            fqdn = self.sf.urlFQDN(eventData.lower())
        else:
            fqdn = eventData
            port = 443

        if fqdn not in self.results:
            self.results[fqdn] = True
        else:
            return None

        self.sf.debug("Testing SSL for: " + fqdn + ':' + str(port))
        # Re-fetch the certificate from the site and process
        try:
            sock = self.sf.safeSSLSocket(fqdn, port, self.opts['ssltimeout'])
            sock.do_handshake()
            dercert = sock.getpeercert(True)
            pemcert = self.sf.sslDerToPem(dercert)
            cert = self.sf.parseCert(str(pemcert), fqdn, self.opts['certexpiringdays'])
        except BaseException as x:
            self.sf.info("Unable to SSL-connect to " + fqdn + " (" + str(x) + ")")
            return None

        if eventName in ['INTERNET_NAME', 'IP_ADDRESS']:
            evt = SpiderFootEvent('TCP_PORT_OPEN', fqdn + ':' + str(port), self.__name__, event)
            self.notifyListeners(evt)

        if not cert.get('text'):
            self.sf.info("Failed to parse the SSL cert for " + fqdn)
            return None

        # Generate the event for the raw cert (in text form)
        # Cert raw data text contains a lot of gems..
        rawevt = SpiderFootEvent("SSL_CERTIFICATE_RAW", cert['text'], self.__name__, event)
        self.notifyListeners(rawevt)

        if cert.get('issued'):
            evt = SpiderFootEvent('SSL_CERTIFICATE_ISSUED', cert['issued'], self.__name__, event)
            self.notifyListeners(evt)

        if cert.get('issuer'):
            evt = SpiderFootEvent('SSL_CERTIFICATE_ISSUER', cert['issuer'], self.__name__, event)
            self.notifyListeners(evt)

        if eventName != "IP_ADDRESS" and cert.get('mismatch'):
            evt = SpiderFootEvent('SSL_CERTIFICATE_MISMATCH', ', '.join(cert.get('hosts')), self.__name__, event)
            self.notifyListeners(evt)

        for san in set(cert.get('altnames', list())):
            dom = san.replace("*.", "")

            if self.getTarget().matches(dom, includeChildren=True):
                evt_type = 'INTERNET_NAME'
            else:
                evt_type = 'AFFILIATE_DOMAIN'

            if self.opts['verify'] and not self.sf.resolveHost(dom):
                    self.sf.debug("Host " + san + " could not be resolved")
                    evt_type += '_UNRESOLVED'

            if "*." not in san:
                evt = SpiderFootEvent(evt_type, san, self.__name__, event)
                self.notifyListeners(evt)

        if cert.get('expired'):
            evt = SpiderFootEvent("SSL_CERTIFICATE_EXPIRED", cert.get('expirystr', 'Unknown'), self.__name__, event)
            self.notifyListeners(evt)
            return None

        if cert.get('expiring'):
            evt = SpiderFootEvent("SSL_CERTIFICATE_EXPIRING", cert.get('expirystr', 'Unknown'), self.__name__, event)
            self.notifyListeners(evt)
            return None

# End of sfp_sslcert class
