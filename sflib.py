#  -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sflib
# Purpose:      Common functions used by SpiderFoot modules.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     26/03/2012
# Copyright:   (c) Steve Micallef 2012
# Licence:     GPL
# -------------------------------------------------------------------------------

import hashlib
import html
import inspect
import io
import json
import os
import random
import re
import socket
import ssl
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from copy import deepcopy
from datetime import datetime

import cryptography
import dns.resolver
import netaddr
import OpenSSL
import requests
import urllib3
from bs4 import BeautifulSoup, SoupStrainer
from networkx import nx
from networkx.readwrite.gexf import GEXFWriter
from publicsuffixlist import PublicSuffixList
from stem import Signal
from stem.control import Controller

# For hiding the SSL warnings coming from the requests lib
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SpiderFoot:
    """SpiderFoot

    Attributes:
        dbh (SpiderFootDb): database handle
        scanId (str): scan ID this instance of SpiderFoot is being used in
        socksProxy (str): SOCKS proxy
        opts (dict): configuration options
    """

    _dbh = None
    _scanId = None
    _socksProxy = None
    opts = dict()

    def __init__(self, options):
        """Initialize SpiderFoot object.

        Args:
            options (dict): dictionary of configuration options.
        """
        if not isinstance(options, dict):
            raise TypeError("options is %s; expected dict()" % type(options))

        self.opts = deepcopy(options)

        # This is ugly but we don't want any fetches to fail - we expect
        # to encounter unverified SSL certs!
        ssl._create_default_https_context = ssl._create_unverified_context

        if self.opts.get('_dnsserver', "") != "":
            res = dns.resolver.Resolver()
            res.nameservers = [self.opts['_dnsserver']]
            dns.resolver.override_system_resolver(res)

    @property
    def dbh(self):
        """Database handle

        Returns:
            SpiderFootDb: database handle
        """
        return self._dbh

    @property
    def scanId(self):
        """Scan instance ID

        Returns:
            str: scan instance ID
        """
        return self._scanId

    @property
    def socksProxy(self):
        """SOCKS proxy

        Returns:
            str: socks proxy
        """
        return self._socksProxy

    @dbh.setter
    def dbh(self, dbh):
        """Called usually some time after instantiation
        to set up a database handle and scan ID, used
        for logging events to the database about a scan.
        """
        self._dbh = dbh

    @scanId.setter
    def scanId(self, scanId):
        """Set the scan ID this instance of SpiderFoot is being used in."""
        self._scanId = scanId

    @socksProxy.setter
    def socksProxy(self, socksProxy):
        """SOCKS proxy

        Bit of a hack to support SOCKS because of the loading order of
        modules. sfscan will call this to update the socket reference
        to the SOCKS one.
        """
        self._socksProxy = socksProxy

    def refreshTorIdent(self):
        """Tell TOR to re-circuit.

        Returns:
            None
        """

        if self.opts['_socks1type'] != "TOR":
            return None

        try:
            self.info("Re-circuiting TOR...")
            with Controller.from_port(address=self.opts['_socks2addr'],
                                      port=self.opts['_torctlport']) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                time.sleep(10)
        except BaseException as e:
            self.fatal(f"Unable to re-circuit TOR: {e}")

        return None

    def optValueToData(self, val, fatal=True, splitLines=True):
        """Supplied an option value, return the data based on what the
        value is. If val is a URL, you'll get back the fetched content,
        if val is a file path it will be loaded and get back the contents,
        and if a string it will simply be returned back.

        Args:
            val (str): TBD
            fatal (bool): TBD
            splitLines (bool): TBD

        Returns:
            str: TBD
        """

        if not isinstance(val, str):
            if fatal:
                self.error(f"Invalid option value {val}")
            else:
                self.error(f"Invalid option value {val}", False)
                return None

        if val.startswith('@'):
            fname = val.split('@')[1]
            try:
                self.info("Loading configuration data from: " + fname)
                f = open(fname, "r")

                if splitLines:
                    arr = f.readlines()
                    ret = list()
                    for x in arr:
                        ret.append(x.rstrip('\n'))
                else:
                    ret = f.read()

                f.close()
                return ret
            except BaseException as e:
                if fatal:
                    self.error(f"Unable to open option file, {fname}: {e}")
                return None

        if val.lower().startswith('http://') or val.lower().startswith('https://'):
            try:
                self.info(f"Downloading configuration data from: {val}")
                session = self.getSession()
                res = session.get(val)

                if splitLines:
                    return res.content.decode('utf-8').splitlines()

                return res.content.decode('utf-8')
            except BaseException as e:
                if fatal:
                    self.error(f"Unable to open option URL, {val}: {e}")
                return None

        return val

    def buildGraphData(self, data, flt=list()):
        """Return a format-agnostic collection of tuples to use as the
        basis for building graphs in various formats.

        Args:
            root (str): TBD
            flt (list): TBD

        Returns:
            set: TBD
        """
        if not data:
            return set()

        mapping = set()
        entities = dict()
        parents = dict()

        def get_next_parent_entities(item, pids):
            ret = list()

            for [parent, entity_id] in parents[item]:
                if entity_id in pids:
                    continue
                if parent in entities:
                    ret.append(parent)
                else:
                    pids.append(entity_id)
                    for p in get_next_parent_entities(parent, pids):
                        ret.append(p)
            return ret

        for row in data:
            if row[11] == "ENTITY" or row[11] == "INTERNAL":
                # List of all valid entity values
                if len(flt) > 0:
                    if row[4] in flt or row[11] == "INTERNAL":
                        entities[row[1]] = True
                else:
                    entities[row[1]] = True

            if row[1] not in parents:
                parents[row[1]] = list()
            parents[row[1]].append([row[2], row[8]])

        for entity in entities:
            for [parent, _id] in parents[entity]:
                if parent in entities:
                    if entity != parent:
                        # print("Adding entity parent: " + parent)
                        mapping.add((entity, parent))
                else:
                    ppids = list()
                    # print("Checking " + parent + " for entityship.")
                    next_parents = get_next_parent_entities(parent, ppids)
                    for next_parent in next_parents:
                        if entity != next_parent:
                            # print("Adding next entity parent: " + next_parent)
                            mapping.add((entity, next_parent))
        return mapping

    def buildGraphGexf(self, root, title, data, flt=[]):
        """Convert supplied raw data into GEXF format (e.g. for Gephi)

        GEXF produced by PyGEXF doesn't work with SigmaJS because
        SJS needs coordinates for each node.
        flt is a list of event types to include, if not set everything is
        included.

        Args:
            root (str): TBD
            title (str): unused
            data (str): TBD
            flt (list): TBD

        Returns:
            str: TBD
        """

        mapping = self.buildGraphData(data, flt)
        graph = nx.Graph()

        nodelist = dict()
        ncounter = 0
        for pair in mapping:
            (dst, src) = pair
            col = ["0", "0", "0"]

            # Leave out this special case
            if dst == "ROOT" or src == "ROOT":
                continue

            if dst not in nodelist:
                ncounter = ncounter + 1
                if dst in root:
                    col = ["255", "0", "0"]
                graph.node[dst]['viz'] = {'color': {'r': col[0], 'g': col[1], 'b': col[2]}}
                nodelist[dst] = ncounter

            if src not in nodelist:
                ncounter = ncounter + 1
                if src in root:
                    col = ["255", "0", "0"]
                graph.add_node(src)
                graph.node[src]['viz'] = {'color': {'r': col[0], 'g': col[1], 'b': col[2]}}
                nodelist[src] = ncounter

            graph.add_edge(src, dst)

        gexf = GEXFWriter(graph=graph)
        return str(gexf).encode('utf-8')

    def buildGraphJson(self, root, data, flt=[]):
        """Convert supplied raw data into JSON format for SigmaJS.

        Args:
            root (str): TBD
            data (str): TBD
            flt (list): TBD

        Returns:
            str: TBD
        """

        mapping = self.buildGraphData(data, flt)
        ret = dict()
        ret['nodes'] = list()
        ret['edges'] = list()

        nodelist = dict()
        ecounter = 0
        ncounter = 0
        for pair in mapping:
            (dst, src) = pair
            col = "#000"

            # Leave out this special case
            if dst == "ROOT" or src == "ROOT":
                continue

            if dst not in nodelist:
                ncounter = ncounter + 1

                if dst in root:
                    col = "#f00"

                ret['nodes'].append({
                    'id': str(ncounter),
                    'label': str(dst),
                    'x': random.SystemRandom().randint(1, 1000),
                    'y': random.SystemRandom().randint(1, 1000),
                    'size': "1",
                    'color': col
                })

                nodelist[dst] = ncounter

            if src not in nodelist:
                ncounter = ncounter + 1

                if src in root:
                    col = "#f00"

                ret['nodes'].append({
                    'id': str(ncounter),
                    'label': str(src),
                    'x': random.SystemRandom().randint(1, 1000),
                    'y': random.SystemRandom().randint(1, 1000),
                    'size': "1",
                    'color': col
                })

                nodelist[src] = ncounter

            ecounter = ecounter + 1

            ret['edges'].append({
                'id': str(ecounter),
                'source': str(nodelist[src]),
                'target': str(nodelist[dst])
            })

        return json.dumps(ret)

    def genScanInstanceId(self):
        """Generate an globally unique ID for this scan.

        Returns:
            str: scan instance unique ID
        """

        return str(uuid.uuid4()).split("-")[0].upper()

    def _dblog(self, level, message, component=None):
        """Log a scan event.

        Args:
            level (str): TBD
            message (str): TBD
            component (str): TBD

        Returns:
            bool: scan event logged successfully
        """

        if not self.dbh:
            self.error("No database handle. Could not log event to database: %s" % message, True)
            return False

        return self.dbh.scanLogEvent(self.scanId, level, message, component)

    def error(self, message, exception=True):
        """Print an error message and optionally also raise an exception.

        Args:
            message (str): error message
            exception (bool): also raise an exception

        Returns:
            None
        """

        if not self.opts['__logging']:
            return None

        if self.dbh is None:
            print(f"[Error] {message}")
        else:
            self._dblog("ERROR", message)
        if self.opts.get('__logstdout'):
            print(f"[Error] {message}")
        if exception:
            raise BaseException(f"Internal Error Encountered: {message}")

        return None

    def fatal(self, error):
        """Print an error message and stacktrace then exit.

        Args:
            error (str): error message

        Returns:
            None
        """

        if self.dbh is None:
            print('[Fatal] %s' % error)
        else:
            self._dblog("FATAL", error)
        print(str(inspect.stack()))
        sys.exit(-1)

    def status(self, message):
        """Log and print a status message.

        Args:
            message (str): status message

        Returns:
            None
        """

        if not self.opts['__logging']:
            return None

        if self.dbh is None:
            print("[Status] %s" % message)
        else:
            self._dblog("STATUS", message)
        if self.opts.get('__logstdout'):
            print("[*] %s" % message)

    def info(self, message):
        """Log and print an info message.

        Args:
            message (str): info message

        Returns:
            None
        """

        if not self.opts['__logging']:
            return None

        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])

        if mod is None:
            modName = "Unknown"
        else:
            if mod.__name__ == "sflib":
                frm = inspect.stack()[2]
                mod = inspect.getmodule(frm[0])
                if mod is None:
                    modName = "Unknown"
                else:
                    modName = mod.__name__
            else:
                modName = mod.__name__

        if self.dbh is None:
            print('[%s] %s' % (modName, message))
        else:
            self._dblog("INFO", message, modName)
        if self.opts.get('__logstdout'):
            print("[*] %s" % message)
        return

    def debug(self, message):
        """Log and print a debug message.

        Args:
            message (str): debug message

        Returns:
            None
        """

        if not self.opts['_debug']:
            return
        if not self.opts['__logging']:
            return None
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])

        if mod is None:
            modName = "Unknown"
        else:
            if mod.__name__ == "sflib":
                frm = inspect.stack()[2]
                mod = inspect.getmodule(frm[0])
                if mod is None:
                    modName = "Unknown"
                else:
                    modName = mod.__name__
            else:
                modName = mod.__name__

        if self.dbh is None:
            print('[%s] %s' % (modName, message))
        else:
            self._dblog("DEBUG", message, modName)
        if self.opts.get('__logstdout'):
            print("[d:%s] %s" % (modName, message))
        return

    @staticmethod
    def myPath():
        # This will get us the program's directory, even if we are frozen using py2exe.

        # Determine whether we've been compiled by py2exe
        if hasattr(sys, "frozen"):
            return os.path.dirname(sys.executable)

        return os.path.dirname(__file__)

    @classmethod
    def dataPath(cls):
        """Returns the file system location of SpiderFoot data and configuration files.

        Returns:
            str: SpiderFoot file system path
        """

        path = os.environ.get('SPIDERFOOT_DATA')
        return path if path is not None else cls.myPath()

    def hashstring(self, string):
        """Returns a SHA256 hash of the specified input.

        Args:
            string (str, list, dict): data to be hashed

        Returns:
            str: SHA256 hash
        """

        s = string
        if type(string) in [list, dict]:
            s = str(string)
        return hashlib.sha256(s.encode('raw_unicode_escape')).hexdigest()

    def cachePath(self):
        """Returns the file system location of the cacha data files.

        Returns:
            str: SpiderFoot cache file system path
        """

        path = self.myPath() + '/cache'
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    def cachePut(self, label, data):
        """Store data to the cache

        Args:
            label (str): TBD
            data (str): TBD
        """

        pathLabel = hashlib.sha224(label.encode('utf-8')).hexdigest()
        cacheFile = self.cachePath() + "/" + pathLabel
        with io.open(cacheFile, "w", encoding="utf-8", errors="ignore") as fp:
            if isinstance(data, list):
                for line in data:
                    if isinstance(line, str):
                        fp.write(line)
                        fp.write("\n")
                    else:
                        fp.write(line.decode('utf-8') + '\n')
            elif isinstance(data, bytes):
                fp.write(data.decode('utf-8'))
            else:
                fp.write(data)

    def cacheGet(self, label, timeoutHrs):
        """Retreive data from the cache

        Args:
            label (str): TBD
            timeoutHrs (str): TBD

        Returns:
            str: cached data
        """

        if label is None:
            return None

        pathLabel = hashlib.sha224(label.encode('utf-8')).hexdigest()
        cacheFile = self.cachePath() + "/" + pathLabel
        try:
            (m, i, d, n, u, g, sz, atime, mtime, ctime) = os.stat(cacheFile)

            if sz == 0:
                return None

            if mtime > time.time() - timeoutHrs * 3600 or timeoutHrs == 0:
                with open(cacheFile, "r") as fp:
                    fileContents = fp.read()
                return fileContents
        except BaseException as e:
            return None

        return None

    def configSerialize(self, opts, filterSystem=True):
        """Convert a Python dictionary to something storable in the database.

        Args:
            opts (dict): TBD
            filterSystem (bool): TBD

        Returns:
            dict: config options
        """

        if not isinstance(opts, dict):
            raise TypeError("opts is %s; expected dict()" % type(opts))

        storeopts = dict()

        if not opts:
            return storeopts

        for opt in list(opts.keys()):
            # Filter out system temporary variables like GUID and others
            if opt.startswith('__') and filterSystem:
                continue

            if isinstance(opts[opt], (int, str)):
                storeopts[opt] = opts[opt]

            if isinstance(opts[opt], bool):
                if opts[opt]:
                    storeopts[opt] = 1
                else:
                    storeopts[opt] = 0
            if isinstance(opts[opt], list):
                storeopts[opt] = ','.join(opts[opt])

        if '__modules__' not in opts:
            return storeopts

        if not isinstance(opts['__modules__'], dict):
            raise TypeError("opts['__modules__'] is %s; expected dict()" % type(opts['__modules__']))

        for mod in opts['__modules__']:
            for opt in opts['__modules__'][mod]['opts']:
                if opt.startswith('_') and filterSystem:
                    continue

                mod_opt = f"{mod}:{opt}"
                mod_opt_val = opts['__modules__'][mod]['opts'][opt]

                if isinstance(mod_opt_val, (int, str)):
                    storeopts[mod_opt] = mod_opt_val

                if isinstance(mod_opt_val, bool):
                    if mod_opt_val:
                        storeopts[mod_opt] = 1
                    else:
                        storeopts[mod_opt] = 0
                if isinstance(mod_opt_val, list):
                    storeopts[mod_opt] = ','.join(str(x) for x in mod_opt_val)

        return storeopts

    def configUnserialize(self, opts, referencePoint, filterSystem=True):
        """Take strings, etc. from the database or UI and convert them
        to a dictionary for Python to process.
        referencePoint is needed to know the actual types the options
        are supposed to be.

        Args:
            opts (dict): TBD
            referencePoint (dict): TBD
            filterSystem (bool): TBD

        Returns:
            dict: TBD
        """

        if not isinstance(opts, dict):
            raise TypeError("opts is %s; expected dict()" % type(opts))
        if not isinstance(referencePoint, dict):
            raise TypeError("referencePoint is %s; expected dict()" % type(referencePoint))

        returnOpts = referencePoint

        # Global options
        for opt in list(referencePoint.keys()):
            if opt.startswith('__') and filterSystem:
                # Leave out system variables
                continue
            if opt in opts:
                if isinstance(referencePoint[opt], bool):
                    if opts[opt] == "1":
                        returnOpts[opt] = True
                    else:
                        returnOpts[opt] = False

                if isinstance(referencePoint[opt], str):
                    returnOpts[opt] = str(opts[opt])

                if isinstance(referencePoint[opt], int):
                    returnOpts[opt] = int(opts[opt])

                if isinstance(referencePoint[opt], list):
                    if isinstance(referencePoint[opt][0], int):
                        returnOpts[opt] = list()
                        for x in str(opts[opt]).split(","):
                            returnOpts[opt].append(int(x))
                    else:
                        returnOpts[opt] = str(opts[opt]).split(",")

        if '__modules__' not in referencePoint:
            return returnOpts

        if not isinstance(referencePoint['__modules__'], dict):
            raise TypeError("referencePoint['__modules__'] is %s; expected dict()" % type(referencePoint['__modules__']))

        # Module options
        # A lot of mess to handle typing..
        for modName in referencePoint['__modules__']:
            for opt in referencePoint['__modules__'][modName]['opts']:
                if opt.startswith('_') and filterSystem:
                    continue

                if modName + ":" + opt in opts:
                    ref_mod = referencePoint['__modules__'][modName]['opts'][opt]
                    if isinstance(ref_mod, bool):
                        if opts[modName + ":" + opt] == "1":
                            returnOpts['__modules__'][modName]['opts'][opt] = True
                        else:
                            returnOpts['__modules__'][modName]['opts'][opt] = False

                    if isinstance(ref_mod, str):
                        returnOpts['__modules__'][modName]['opts'][opt] = str(opts[modName + ":" + opt])

                    if isinstance(ref_mod, int):
                        returnOpts['__modules__'][modName]['opts'][opt] = int(opts[modName + ":" + opt])

                    if isinstance(ref_mod, list):
                        if isinstance(ref_mod[0], int):
                            returnOpts['__modules__'][modName]['opts'][opt] = list()
                            for x in str(opts[modName + ":" + opt]).split(","):
                                returnOpts['__modules__'][modName]['opts'][opt].append(int(x))
                        else:
                            returnOpts['__modules__'][modName]['opts'][opt] = str(opts[modName + ":" + opt]).split(",")

        return returnOpts

    def targetType(self, target):
        """Return the scan target seed data type for the specified scan target input.

        Args:
            target (str): scan target seed input

        Returns:
            str: scan target seed data type
        """
        if not target:
            return None

        targetType = None

        regexToType = [
            {r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$": "IP_ADDRESS"},
            {r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/\d+$": "NETBLOCK_OWNER"},
            {r"^.*@.*$": "EMAILADDR"},
            {r"^\+[0-9]+$": "PHONE_NUMBER"},
            {r"^\".+\s+.+\"$": "HUMAN_NAME"},
            {r"^\".+\"$": "USERNAME"},
            {r"^[0-9]+$": "BGP_AS_OWNER"},
            {r"^[0-9a-f:]+$": "IPV6_ADDRESS"},
            {r"^(([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])\.)+([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$": "INTERNET_NAME"}
        ]

        # Parse the target and set the targetType
        for rxpair in regexToType:
            rx = list(rxpair.keys())[0]
            if re.match(rx, target, re.IGNORECASE | re.UNICODE):
                targetType = list(rxpair.values())[0]
                break
        return targetType

    def modulesProducing(self, events):
        """Return an array of modules that produce the list of types supplied.

        Args:
            events (list): list of event types

        Returns:
            list: list of modules
        """
        modlist = list()

        if not events:
            return modlist

        loaded_modules = self.opts.get('__modules__')

        if not loaded_modules:
            return modlist

        for mod in list(loaded_modules.keys()):
            provides = loaded_modules[mod].get('provides')

            if not provides:
                continue

            if "*" in events:
                modlist.append(mod)

            for evtype in provides:
                if evtype in events:
                    modlist.append(mod)

        return list(set(modlist))

    def modulesConsuming(self, events):
        """Return an array of modules that consume the list of types supplied.

        Args:
            events (list): list of event types

        Returns:
            list: list of modules
        """
        modlist = list()

        if not events:
            return modlist

        loaded_modules = self.opts.get('__modules__')

        if not loaded_modules:
            return modlist

        for mod in list(loaded_modules.keys()):
            consumes = loaded_modules[mod].get('consumes')

            if not consumes:
                continue

            if "*" in consumes:
                modlist.append(mod)
                continue

            for evtype in consumes:
                if evtype in events:
                    modlist.append(mod)

        return list(set(modlist))

    def eventsFromModules(self, modules):
        """Return an array of types that are produced by the list of modules supplied.

        Args:
            modules (list): list of modules

        Returns:
            list: list of types
        """
        evtlist = list()

        if not modules:
            return evtlist

        loaded_modules = self.opts.get('__modules__')

        if not loaded_modules:
            return evtlist

        for mod in modules:
            if mod in list(loaded_modules.keys()):
                provides = loaded_modules[mod].get('provides')
                if provides:
                    for evt in provides:
                        evtlist.append(evt)

        return evtlist

    def eventsToModules(self, modules):
        """Return an array of types that are consumed by the list of modules supplied.

        Args:
            modules (list): list of modules

        Returns:
            list: list of types
        """
        evtlist = list()

        if not modules:
            return evtlist

        loaded_modules = self.opts.get('__modules__')

        if not loaded_modules:
            return evtlist

        for mod in modules:
            if mod in list(loaded_modules.keys()):
                consumes = loaded_modules[mod].get('consumes')
                if consumes:
                    for evt in consumes:
                        evtlist.append(evt)

        return evtlist

    def urlRelativeToAbsolute(self, url):
        """Turn a relative path into an absolute path

        Args:
            url (str): URL

        Returns:
            str: URL relative path
        """

        if not url:
            self.error("Invalid URL: %s" % url, False)
            return None

        finalBits = list()

        if '..' not in url:
            return url

        bits = url.split('/')

        for chunk in bits:
            if chunk == '..':
                # Don't pop the last item off if we're at the top
                if len(finalBits) <= 1:
                    continue

                # Don't pop the last item off if the first bits are not the path
                if '://' in url and len(finalBits) <= 3:
                    continue

                finalBits.pop()
                continue

            finalBits.append(chunk)

        return '/'.join(finalBits)

    def urlBaseDir(self, url):
        """Extract the top level directory from a URL

        Args:
            url (str): URL

        Returns:
            str: base directory
        """

        if not url:
            self.error("Invalid URL: %s" % url, False)
            return None

        bits = url.split('/')

        # For cases like 'www.somesite.com'
        if len(bits) == 0:
            return url + '/'

        # For cases like 'http://www.blah.com'
        if '://' in url and url.count('/') < 3:
            return url + '/'

        base = '/'.join(bits[:-1])

        return base + '/'

    def urlBaseUrl(self, url):
        """Extract the scheme and domain from a URL

        Does not return the trailing slash! So you can do .endswith() checks.

        Args:
            url (str): URL

        Returns:
            str: base URL without trailing slash
        """

        if not url:
            self.error("Invalid URL: %s" % url, False)
            return None

        if '://' in url:
            bits = re.match(r'(\w+://.[^/:\?]*)[:/\?].*', url)
        else:
            bits = re.match(r'(.[^/:\?]*)[:/\?]', url)

        if bits is None:
            return url.lower()

        return bits.group(1).lower()

    def urlFQDN(self, url):
        """Extract the FQDN from a URL.

        Args:
            url (str): URL

        Returns:
            str: FQDN
        """

        if not url:
            self.error(f"Invalid URL: {url}", False)
            return None

        baseurl = self.urlBaseUrl(url)
        if '://' in baseurl:
            count = 2
        else:
            count = 0

        # http://abc.com will split to ['http:', '', 'abc.com']
        return baseurl.split('/')[count].lower()

    def domainKeyword(self, domain, tldList):
        """Extract the keyword (the domain without the TLD or any subdomains) from a domain.

        Args:
            domain (str): The domain to check.
            tldList (str): The list of TLDs based on the Mozilla public list.

        Returns:
            str: The keyword
        """

        if not domain:
            self.error(f"Invalid domain: {domain}", False)
            return None

        # Strip off the TLD
        dom = self.hostDomain(domain.lower(), tldList)
        if not dom:
            return None

        tld = '.'.join(dom.split('.')[1:])
        ret = domain.lower().replace('.' + tld, '')

        # If the user supplied a domain with a sub-domain, return the second part
        if '.' in ret:
            return ret.split('.')[-1]

        return ret

    def domainKeywords(self, domainList, tldList):
        """Extract the keywords (the domains without the TLD or any subdomains) from a list of domains.

        Args:
            domainList (list): The list of domains to check.
            tldList (str): The list of TLDs based on the Mozilla public list.

        Returns:
            set: List of keywords
        """

        if not domainList:
            self.error("Invalid domain list: %s" % domainList, False)
            return set()

        keywords = list()
        for domain in domainList:
            keywords.append(self.domainKeyword(domain, tldList))

        self.debug("Keywords: %s" % keywords)
        return set([k for k in keywords if k])

    def hostDomain(self, hostname, tldList):
        """Obtain the domain name for a supplied hostname.

        Args:
            hostname (str): The hostname to check.
            tldList (str): The list of TLDs based on the Mozilla public list.

        Returns:
            str: The domain name.
        """

        if not tldList:
            return None
        if not hostname:
            return None

        ps = PublicSuffixList(tldList, only_icann=True)
        return ps.privatesuffix(hostname)

    def validHost(self, hostname, tldList):
        """Check if the provided string is a valid hostname with a valid public suffix TLD.

        Args:
            hostname (str): The hostname to check.
            tldList (str): The list of TLDs based on the Mozilla public list.

        Returns:
            bool
        """

        if not tldList:
            return False
        if not hostname:
            return False

        if "." not in hostname:
            return False

        if not re.match(r"^[a-z0-9-\.]*$", hostname, re.IGNORECASE):
            return False

        ps = PublicSuffixList(tldList, only_icann=True, accept_unknown=False)
        sfx = ps.privatesuffix(hostname)
        return sfx is not None

    def isDomain(self, hostname, tldList):
        """Check if the provided hostname string is a valid domain name.

        Given a possible hostname, check if it's a domain name
        By checking whether it rests atop a valid TLD.
        e.g. www.example.com = False because tld of hostname is com,
        and www.example has a . in it.

        Args:
            hostname (str): The hostname to check.
            tldList (str): The list of TLDs based on the Mozilla public list.

        Returns:
            bool
        """

        if not tldList:
            return False
        if not hostname:
            return False

        ps = PublicSuffixList(tldList, only_icann=True, accept_unknown=False)
        sfx = ps.privatesuffix(hostname)
        return sfx == hostname

    def validIP(self, address):
        """Check if the provided string is a valid IPv4 address.

        Args:
            address (str): The IPv4 address to check.

        Returns:
            bool
        """

        if not address:
            return False
        return netaddr.valid_ipv4(address)

    def validIP6(self, address):
        """Check if the provided string is a valid IPv6 address.

        Args:
            address (str): The IPv6 address to check.

        Returns:
            bool: string is a valid IPv6 address
        """

        if not address:
            return False
        return netaddr.valid_ipv6(address)

    def validIpNetwork(self, cidr):
        """Check if the provided string is a valid CIDR netblock.

        Args:
            cidr (str): The netblock to check.

        Returns:
            bool: string is a valid CIDR netblock
        """
        if not isinstance(cidr, str):
            return False

        if '/' not in cidr:
            return False

        try:
            return bool(netaddr.IPNetwork(str(cidr)).size > 0)
        except BaseException:
            return False

    def isPublicIpAddress(self, ip):
        """Check if an IP address is public.

        Args:
            ip (str): IP address

        Returns:
            bool: IP address is public
        """
        if not isinstance(ip, (str, netaddr.IPAddress)):
            return False
        if not self.validIP(ip) and not self.validIP6(ip):
            return False

        if not netaddr.IPAddress(ip).is_unicast():
            return False

        if netaddr.IPAddress(ip).is_loopback():
            return False
        if netaddr.IPAddress(ip).is_reserved():
            return False
        if netaddr.IPAddress(ip).is_multicast():
            return False
        if netaddr.IPAddress(ip).is_private():
            return False
        return True

    def normalizeDNS(self, res):
        """Clean DNS results to be a simple list

        Args:
            res (list): List of DNS names

        Returns:
            list: list of domains
        """

        ret = list()

        if not res:
            return ret

        for addr in res:
            if isinstance(addr, list):
                for host in addr:
                    host = str(host).rstrip(".")
                    if host:
                        ret.append(host)
            else:
                host = str(addr).rstrip(".")
                if host:
                    ret.append(host)
        return ret

    def validEmail(self, email):
        """Check if the provided string is a valid email address.

        Args:
            email (str): The email address to check.

        Returns:
            bool: email is a valid email address
        """

        if not isinstance(email, str):
            return False

        if "@" not in email:
            return False

        if not re.match(r'^([\%a-zA-Z\.0-9_\-\+]+@[a-zA-Z\.0-9\-]+\.[a-zA-Z\.0-9\-]+)$', email):
            return False

        if len(email) < 6:
            return False

        # Handle messed up encodings
        if "%" in email:
            return False

        # Handle truncated emails
        if "..." in email:
            return False

        return True

    def sanitiseInput(self, cmd):
        """Verify input command is safe to execute

        Args:
            cmd (str): The command to check

        Returns:
            bool: command is "safe"
        """

        chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                 '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.']
        for c in cmd:
            if c.lower() not in chars:
                return False

        if '..' in cmd:
            return False

        if cmd.startswith("-"):
            return False

        if len(cmd) < 3:
            return False

        return True

    def dictwords(self):
        """Return dictionary words and/or names from several language dictionaries

        Returns:
            list: words and names from dictionaries
        """

        wd = dict()

        dicts = ["english", "german", "french", "spanish"]

        for d in dicts:
            try:
                with io.open(self.myPath() + "/dicts/ispell/" + d + ".dict", 'r', encoding='utf8', errors='ignore') as wdct:
                    dlines = wdct.readlines()
            except BaseException as e:
                self.debug(f"Could not read dictionary: {e}")
                continue

            for w in dlines:
                w = w.strip().lower()
                wd[w.split('/')[0]] = True

        return list(wd.keys())

    def dictnames(self):
        """Return names of available dictionary files.

        Returns:
            list: list of dictionary file names.
        """

        wd = dict()

        dicts = ["names"]

        for d in dicts:
            try:
                wdct = open(self.myPath() + "/dicts/ispell/" + d + ".dict", 'r')
                dlines = wdct.readlines()
                wdct.close()
            except BaseException as e:
                self.debug("Could not read dictionary: " + str(e))
                continue

            for w in dlines:
                w = w.strip().lower()
                wd[w.split('/')[0]] = True

        return list(wd.keys())

    def dataParentChildToTree(self, data):
        """Converts a dictionary of k -> array to a nested
        tree that can be digested by d3 for visualizations.

        Args:
            data (dict): dictionary of k -> array

        Returns:
            dict: nested tree
        """

        if not isinstance(data, dict):
            self.error("Data is not a dict", False)
            return {}

        def get_children(needle, haystack):
            ret = list()

            if needle not in list(haystack.keys()):
                return None

            if haystack[needle] is None:
                return None

            for c in haystack[needle]:
                ret.append({"name": c, "children": get_children(c, haystack)})
            return ret

        # Find the element with no parents, that's our root.
        root = None
        for k in list(data.keys()):
            if data[k] is None:
                continue

            contender = True
            for ck in list(data.keys()):
                if data[ck] is None:
                    continue

                if k in data[ck]:
                    contender = False

            if contender:
                root = k
                break

        if root is None:
            return {}

        return {"name": root, "children": get_children(root, data)}

    def resolveHost(self, host):
        """Return a normalised resolution of a hostname.

        Args:
            host (str): host to resolve

        Returns:
            list: IP addresses
        """

        addrs = list()

        if not host:
            self.error("Unable to resolve %s (Invalid host)" % host, False)
            return addrs

        try:
            addrs = self.normalizeDNS(socket.gethostbyname_ex(host))
        except BaseException as e:
            self.debug("Unable to resolve %s (%s)" % (host, e))

        if len(addrs):
            self.debug("Resolved %s to: %s" % (host, addrs))

        return list(set(addrs))

    def resolveIP(self, ipaddr):
        """Return a normalised resolution of an IPv4 address.

        Args:
            ipaddr (str): IP address to reverse resolve

        Returns:
            list: list of domain names
        """

        addrs = list()

        if not self.validIP(ipaddr) and not self.validIP6(ipaddr):
            self.error("Unable to resolve %s (Invalid IP address)" % ipaddr, False)
            return addrs

        self.debug("Performing reverse-resolve of %s" % ipaddr)

        try:
            addrs = self.normalizeDNS(socket.gethostbyaddr(ipaddr))
        except BaseException as e:
            self.debug("Unable to resolve %s (%s)" % (ipaddr, e))

        if len(addrs):
            self.debug("Resolved %s to: %s" % (ipaddr, addrs))

        return list(set(addrs))

    def resolveHost6(self, hostname):
        """Return a normalised resolution of an IPv6 address.

        Args:
            hostname (str): hostname to reverse resolve

        Returns:
            list
        """

        addrs = list()

        if not hostname:
            self.error("Unable to resolve %s (Invalid hostname)" % hostname, False)
            return addrs

        try:
            res = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            for addr in res:
                if addr[4][0] not in addrs:
                    addrs.append(addr[4][0])
        except BaseException as e:
            self.debug("Unable to IPv6 resolve %s (%s)" % (hostname, e))

        if len(addrs):
            self.debug("Resolved %s to IPv6: %s" % (hostname, addrs))

        return list(set(addrs))

    def validateIP(self, host, ip):
        """Verify a host resolves to a given IP."""

        addrs = self.resolveHost(host)

        if not addrs:
            return False

        for addr in addrs:
            if str(addr) == ip:
                return True

        return False

    def resolveTargets(self, target, validateReverse):
        """Resolve alternative names for a given target.

        Args:
            target (SpiderFootTarget): target object
            validateReverse (bool): validate domain names resolve

        Returns:
            list: list of domain names and IP addresses
        """
        ret = list()

        if not target:
            return ret

        t = target.targetType
        v = target.targetValue

        if t in ["IP_ADDRESS", "IPV6_ADDRESS"]:
            r = self.resolveIP(v)
            if r:
                ret.extend(r)
        if t == "INTERNET_NAME":
            r = self.resolveHost(v)
            if r:
                ret.extend(r)
        if t == "NETBLOCK_OWNER":
            for addr in netaddr.IPNetwork(v):
                ipaddr = str(addr)
                if ipaddr.split(".")[3] in ['255', '0']:
                    continue
                if '255' in ipaddr.split("."):
                    continue
                ret.append(ipaddr)

                # Add the reverse-resolved hostnames as aliases too..
                names = self.resolveIP(ipaddr)
                if names:
                    if validateReverse:
                        for host in names:
                            chk = self.resolveHost(host)
                            if chk:
                                if ipaddr in chk:
                                    ret.append(host)
                    else:
                        ret.extend(names)
        return list(set(ret))

    def safeSocket(self, host, port, timeout):
        """Create a safe socket that's using SOCKS/TOR if it was enabled."""
        sock = socket.create_connection((host, int(port)), int(timeout))
        sock.settimeout(int(timeout))
        return sock

    def safeSSLSocket(self, host, port, timeout):
        """Create a safe SSL connection that's using SOCKs/TOR if it was enabled."""
        s = socket.socket()
        s.settimeout(int(timeout))
        s.connect((host, int(port)))
        sock = ssl.wrap_socket(s)
        sock.do_handshake()
        return sock

    def parseRobotsTxt(self, robotsTxtData):
        """Parse the contents of robots.txt.

        Args:
            robotsTxtData (str): robots.txt file contents

        Returns:
            list: list of patterns which should not be followed

        Todo:
            We don't check the User-Agent rule yet.. probably should at some stage

            fix whitespace parsing; ie, " " is not a valid disallowed path
        """

        returnArr = list()

        if not isinstance(robotsTxtData, str):
            return returnArr

        for line in robotsTxtData.splitlines():
            if line.lower().startswith('disallow:'):
                m = re.match(r'disallow:\s*(.[^ #]*)', line, re.IGNORECASE)
                if m:
                    self.debug('robots.txt parsing found disallow: ' + m.group(1))
                    returnArr.append(m.group(1))

        return returnArr

    def parseHashes(self, data):
        """Extract all hashes within the supplied content.

        Args:
            data (str): text to search for hashes

        Returns:
            list: list of hashes
        """

        ret = list()

        if not isinstance(data, str):
            return ret

        hashes = {
            "MD5": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{32})(?:[^a-fA-F\d]|\b)"),
            "SHA1": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{40})(?:[^a-fA-F\d]|\b)"),
            "SHA256": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{64})(?:[^a-fA-F\d]|\b)"),
            "SHA512": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{128})(?:[^a-fA-F\d]|\b)")
        }

        for h in hashes:
            matches = re.findall(hashes[h], data)
            for match in matches:
                self.debug("Found hash: " + match)
                ret.append((h, match))

        return ret

    def parseEmails(self, data):
        """Extract all email addresses within the supplied content.

        Args:
            data (str): text to search for email addresses

        Returns:
            list: list of email addresses
        """

        if not isinstance(data, str):
            return list()

        emails = set()
        matches = re.findall(r'([\%a-zA-Z\.0-9_\-\+]+@[a-zA-Z\.0-9\-]+\.[a-zA-Z\.0-9\-]+)', data)

        for match in matches:
            if self.validEmail(match):
                emails.add(match)

        return list(emails)

    def parseCreditCards(self, data):
        """Find all credit card numbers with the supplied content.

        Extracts numbers with lengths ranging from 13 - 19 digits

        Checks the numbers using Luhn's algorithm to verify
        if the number is a valid credit card number or not

        Args:
            data (str): text to search for credit card numbers

        Returns:
            list: list of credit card numbers
        """

        if not isinstance(data, str):
            return list()

        creditCards = set()

        # Remove whitespace from data.
        # Credit cards might contain spaces between them
        # which will cause regex mismatch
        data = data.replace(" ", "")

        # Extract all numbers with lengths ranging from 13 - 19 digits
        matches = re.findall(r"[0-9]{13,19}", data)

        # Verify each extracted number using Luhn's algorithm
        for match in matches:

            if int(match) == 0:
                self.debug("Skipped invalid credit card number: " + match)
                continue

            ccNumber = match

            ccNumberTotal = 0
            isSecondDigit = False

            for digit in ccNumber[::-1]:
                d = int(digit)
                if isSecondDigit:
                    d *= 2
                ccNumberTotal += int(d / 10)
                ccNumberTotal += d % 10

                isSecondDigit = not isSecondDigit
            if ccNumberTotal % 10 == 0:
                self.debug("Found credit card number: " + match)
                creditCards.add(match)
            else:
                self.debug("Skipped invalid credit card number: " + match)
        return list(creditCards)

    def getCountryCodeDict(self):
        """Dictionary of country codes and associated country names.

        Returns:
            dict: country codes and associated country names
        """

        return {
            "AF": "Afghanistan",
            "AX": "Aland Islands",
            "AL": "Albania",
            "DZ": "Algeria",
            "AS": "American Samoa",
            "AD": "Andorra",
            "AO": "Angola",
            "AI": "Anguilla",
            "AQ": "Antarctica",
            "AG": "Antigua and Barbuda",
            "AR": "Argentina",
            "AM": "Armenia",
            "AW": "Aruba",
            "AU": "Australia",
            "AT": "Austria",
            "AZ": "Azerbaijan",
            "BS": "Bahamas",
            "BH": "Bahrain",
            "BD": "Bangladesh",
            "BB": "Barbados",
            "BY": "Belarus",
            "BE": "Belgium",
            "BZ": "Belize",
            "BJ": "Benin",
            "BM": "Bermuda",
            "BT": "Bhutan",
            "BO": "Bolivia",
            "BQ": "Bonaire, Saint Eustatius and Saba",
            "BA": "Bosnia and Herzegovina",
            "BW": "Botswana",
            "BV": "Bouvet Island",
            "BR": "Brazil",
            "IO": "British Indian Ocean Territory",
            "VG": "British Virgin Islands",
            "BN": "Brunei",
            "BG": "Bulgaria",
            "BF": "Burkina Faso",
            "BI": "Burundi",
            "KH": "Cambodia",
            "CM": "Cameroon",
            "CA": "Canada",
            "CV": "Cape Verde",
            "KY": "Cayman Islands",
            "CF": "Central African Republic",
            "TD": "Chad",
            "CL": "Chile",
            "CN": "China",
            "CX": "Christmas Island",
            "CC": "Cocos Islands",
            "CO": "Colombia",
            "KM": "Comoros",
            "CK": "Cook Islands",
            "CR": "Costa Rica",
            "HR": "Croatia",
            "CU": "Cuba",
            "CW": "Curacao",
            "CY": "Cyprus",
            "CZ": "Czech Republic",
            "CD": "Democratic Republic of the Congo",
            "DK": "Denmark",
            "DJ": "Djibouti",
            "DM": "Dominica",
            "DO": "Dominican Republic",
            "TL": "East Timor",
            "EC": "Ecuador",
            "EG": "Egypt",
            "SV": "El Salvador",
            "GQ": "Equatorial Guinea",
            "ER": "Eritrea",
            "EE": "Estonia",
            "ET": "Ethiopia",
            "FK": "Falkland Islands",
            "FO": "Faroe Islands",
            "FJ": "Fiji",
            "FI": "Finland",
            "FR": "France",
            "GF": "French Guiana",
            "PF": "French Polynesia",
            "TF": "French Southern Territories",
            "GA": "Gabon",
            "GM": "Gambia",
            "GE": "Georgia",
            "DE": "Germany",
            "GH": "Ghana",
            "GI": "Gibraltar",
            "GR": "Greece",
            "GL": "Greenland",
            "GD": "Grenada",
            "GP": "Guadeloupe",
            "GU": "Guam",
            "GT": "Guatemala",
            "GG": "Guernsey",
            "GN": "Guinea",
            "GW": "Guinea-Bissau",
            "GY": "Guyana",
            "HT": "Haiti",
            "HM": "Heard Island and McDonald Islands",
            "HN": "Honduras",
            "HK": "Hong Kong",
            "HU": "Hungary",
            "IS": "Iceland",
            "IN": "India",
            "ID": "Indonesia",
            "IR": "Iran",
            "IQ": "Iraq",
            "IE": "Ireland",
            "IM": "Isle of Man",
            "IL": "Israel",
            "IT": "Italy",
            "CI": "Ivory Coast",
            "JM": "Jamaica",
            "JP": "Japan",
            "JE": "Jersey",
            "JO": "Jordan",
            "KZ": "Kazakhstan",
            "KE": "Kenya",
            "KI": "Kiribati",
            "XK": "Kosovo",
            "KW": "Kuwait",
            "KG": "Kyrgyzstan",
            "LA": "Laos",
            "LV": "Latvia",
            "LB": "Lebanon",
            "LS": "Lesotho",
            "LR": "Liberia",
            "LY": "Libya",
            "LI": "Liechtenstein",
            "LT": "Lithuania",
            "LU": "Luxembourg",
            "MO": "Macao",
            "MK": "Macedonia",
            "MG": "Madagascar",
            "MW": "Malawi",
            "MY": "Malaysia",
            "MV": "Maldives",
            "ML": "Mali",
            "MT": "Malta",
            "MH": "Marshall Islands",
            "MQ": "Martinique",
            "MR": "Mauritania",
            "MU": "Mauritius",
            "YT": "Mayotte",
            "MX": "Mexico",
            "FM": "Micronesia",
            "MD": "Moldova",
            "MC": "Monaco",
            "MN": "Mongolia",
            "ME": "Montenegro",
            "MS": "Montserrat",
            "MA": "Morocco",
            "MZ": "Mozambique",
            "MM": "Myanmar",
            "NA": "Namibia",
            "NR": "Nauru",
            "NP": "Nepal",
            "NL": "Netherlands",
            "AN": "Netherlands Antilles",
            "NC": "New Caledonia",
            "NZ": "New Zealand",
            "NI": "Nicaragua",
            "NE": "Niger",
            "NG": "Nigeria",
            "NU": "Niue",
            "NF": "Norfolk Island",
            "KP": "North Korea",
            "MP": "Northern Mariana Islands",
            "NO": "Norway",
            "OM": "Oman",
            "PK": "Pakistan",
            "PW": "Palau",
            "PS": "Palestinian Territory",
            "PA": "Panama",
            "PG": "Papua New Guinea",
            "PY": "Paraguay",
            "PE": "Peru",
            "PH": "Philippines",
            "PN": "Pitcairn",
            "PL": "Poland",
            "PT": "Portugal",
            "PR": "Puerto Rico",
            "QA": "Qatar",
            "CG": "Republic of the Congo",
            "RE": "Reunion",
            "RO": "Romania",
            "RU": "Russia",
            "RW": "Rwanda",
            "BL": "Saint Barthelemy",
            "SH": "Saint Helena",
            "KN": "Saint Kitts and Nevis",
            "LC": "Saint Lucia",
            "MF": "Saint Martin",
            "PM": "Saint Pierre and Miquelon",
            "VC": "Saint Vincent and the Grenadines",
            "WS": "Samoa",
            "SM": "San Marino",
            "ST": "Sao Tome and Principe",
            "SA": "Saudi Arabia",
            "SN": "Senegal",
            "RS": "Serbia",
            "CS": "Serbia and Montenegro",
            "SC": "Seychelles",
            "SL": "Sierra Leone",
            "SG": "Singapore",
            "SX": "Sint Maarten",
            "SK": "Slovakia",
            "SI": "Slovenia",
            "SB": "Solomon Islands",
            "SO": "Somalia",
            "ZA": "South Africa",
            "GS": "South Georgia and the South Sandwich Islands",
            "KR": "South Korea",
            "SS": "South Sudan",
            "ES": "Spain",
            "LK": "Sri Lanka",
            "SD": "Sudan",
            "SR": "Suriname",
            "SJ": "Svalbard and Jan Mayen",
            "SZ": "Swaziland",
            "SE": "Sweden",
            "CH": "Switzerland",
            "SY": "Syria",
            "TW": "Taiwan",
            "TJ": "Tajikistan",
            "TZ": "Tanzania",
            "TH": "Thailand",
            "TG": "Togo",
            "TK": "Tokelau",
            "TO": "Tonga",
            "TT": "Trinidad and Tobago",
            "TN": "Tunisia",
            "TR": "Turkey",
            "TM": "Turkmenistan",
            "TC": "Turks and Caicos Islands",
            "TV": "Tuvalu",
            "VI": "U.S. Virgin Islands",
            "UG": "Uganda",
            "UA": "Ukraine",
            "AE": "United Arab Emirates",
            "GB": "United Kingdom",
            "US": "United States",
            "UM": "United States Minor Outlying Islands",
            "UY": "Uruguay",
            "UZ": "Uzbekistan",
            "VU": "Vanuatu",
            "VA": "Vatican",
            "VE": "Venezuela",
            "VN": "Vietnam",
            "WF": "Wallis and Futuna",
            "EH": "Western Sahara",
            "YE": "Yemen",
            "ZM": "Zambia",
            "ZW": "Zimbabwe",
            # Below are not country codes but recognized as regions / TLDs
            "AC": "Ascension Island",
            "EU": "European Union",
            "SU": "Soviet Union",
            "UK": "United Kingdom"
        }

    def countryNameFromCountryCode(self, countryCode):
        """Convert a country code to full country name

        Args:
            countryCode (str): country code

        Returns:
            str: country name
        """
        if not isinstance(countryCode, str):
            return None

        return self.getCountryCodeDict().get(countryCode.upper())

    def countryNameFromTld(self, tld):
        """Retrieve the country name associated with a TLD.

        Args:
            tld (str): Top level domain

        Returns:
            str: country name
        """

        if not isinstance(tld, str):
            return None

        country_name = self.getCountryCodeDict().get(tld.upper())

        if country_name:
            return country_name

        country_tlds = {
            # List of TLD not associated with any country
            "COM": "United States",
            "NET": "United States",
            "ORG": "United States",
            "GOV": "United States",
            "MIL": "United States"
        }

        country_name = country_tlds.get(tld.upper())

        if country_name:
            return country_name

        return None

    def parseIBANNumbers(self, data):
        """Find all International Bank Account Numbers (IBANs) within the supplied content.

        Extracts possible IBANs using a generic regex.

        Checks whether possible IBANs are valid or not
        using country-wise length check and Mod 97 algorithm.

        Args:
            data (str): text to search for IBANs

        Returns:
            list: list of IBAN
        """
        if not isinstance(data, str):
            return list()

        ibans = set()

        # Dictionary of country codes and their respective IBAN lengths
        ibanCountryLengths = {
            "AL": 28, "AD": 24, "AT": 20, "AZ": 28,
            "ME": 22, "BH": 22, "BY": 28, "BE": 16,
            "BA": 20, "BR": 29, "BG": 22, "CR": 22,
            "HR": 21, "CY": 28, "CZ": 24, "DK": 18,
            "DO": 28, "EG": 29, "SV": 28, "FO": 18,
            "FI": 18, "FR": 27, "GE": 22, "DE": 22,
            "GI": 23, "GR": 27, "GL": 18, "GT": 28,
            "VA": 22, "HU": 28, "IS": 26, "IQ": 23,
            "IE": 22, "IL": 23, "JO": 30, "KZ": 20,
            "XK": 20, "KW": 30, "LV": 21, "LB": 28,
            "LI": 21, "LT": 20, "LU": 20, "MT": 31,
            "MR": 27, "MU": 30, "MD": 24, "MC": 27,
            "DZ": 24, "AO": 25, "BJ": 28, "VG": 24,
            "BF": 27, "BI": 16, "CM": 27, "CV": 25,
            "CG": 27, "EE": 20, "GA": 27, "GG": 22,
            "IR": 26, "IM": 22, "IT": 27, "CI": 28,
            "JE": 22, "MK": 19, "MG": 27, "ML": 28,
            "MZ": 25, "NL": 18, "NO": 15, "PK": 24,
            "PS": 29, "PL": 28, "PT": 25, "QA": 29,
            "RO": 24, "LC": 32, "SM": 27, "ST": 25,
            "SA": 24, "SN": 28, "RS": 22, "SC": 31,
            "SK": 24, "SI": 19, "ES": 24, "CH": 21,
            "TL": 23, "TN": 24, "TR": 26, "UA": 29,
            "AE": 23, "GB": 22, "SE": 24
        }

        # Normalize input data to remove whitespace
        data = data.replace(" ", "")

        # Extract alphanumeric characters of lengths ranging from 15 to 32
        # and starting with two characters
        matches = re.findall("[A-Za-z]{2}[A-Za-z0-9]{13,30}", data)

        for match in matches:
            iban = match.upper()

            countryCode = iban[0:2]

            if countryCode not in ibanCountryLengths.keys():
                self.debug("Skipped invalid IBAN (invalid country code): %s" % iban)
                continue

            if len(iban) != ibanCountryLengths[countryCode]:
                self.debug("Skipped invalid IBAN (invalid length): %s" % iban)
                continue

            # Convert IBAN to integer format.
            # Move the first 4 characters to the end of the string,
            # then convert all characters to integers; where A = 10, B = 11, ...., Z = 35
            iban_int = iban[4:] + iban[0:4]
            for character in iban_int:
                if character.isalpha():
                    iban_int = iban_int.replace(character, str((ord(character) - 65) + 10))

            # Check IBAN integer mod 97 for remainder
            if int(iban_int) % 97 != 1:
                self.debug("Skipped invalid IBAN: %s" % iban)
                continue

            self.debug("Found IBAN: %s" % iban)
            ibans.add(iban)

        return list(ibans)

    def sslDerToPem(self, der_cert):
        """Given a certificate as a DER-encoded blob of bytes, returns a PEM-encoded string version of the same certificate.

        Args:
            der_cert (bytes): certificate in DER format

        Returns:
            str: PEM-encoded certificate as a byte string
        """

        if not isinstance(der_cert, bytes):
            raise TypeError("der_cert is %s; expected bytes()" % type(der_cert))

        return ssl.DER_cert_to_PEM_cert(der_cert)

    def parseCert(self, rawcert, fqdn=None, expiringdays=30):
        """Parse a PEM-format SSL certificate.

        Args:
            rawcert (str): TBD
            fqdn (str): TBD
            expiringdays (int): TBD

        Returns:
            dict: certificate details
        """

        if not rawcert:
            self.error(f"Invalid certificate: {rawcert}", False)
            return None

        ret = dict()
        if '\r' in rawcert:
            rawcert = rawcert.replace('\r', '')
        if isinstance(rawcert, str):
            rawcert = rawcert.encode('utf-8')

        from cryptography.hazmat.backends.openssl import backend
        cert = cryptography.x509.load_pem_x509_certificate(rawcert, backend)
        sslcert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, rawcert)
        sslcert_dump = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_TEXT, sslcert)

        ret['text'] = sslcert_dump.decode('utf-8', errors='replace')
        ret['issuer'] = str(cert.issuer)
        ret['altnames'] = list()
        ret['expired'] = False
        ret['expiring'] = False
        ret['mismatch'] = False
        ret['certerror'] = False
        ret['issued'] = str(cert.subject)

        # Expiry info
        try:
            notafter = datetime.strptime(sslcert.get_notAfter().decode('utf-8'), "%Y%m%d%H%M%SZ")
            ret['expiry'] = int(notafter.strftime("%s"))
            ret['expirystr'] = notafter.strftime("%Y-%m-%d %H:%M:%S")
            now = int(time.time())
            warnexp = now + (expiringdays * 86400)
            if ret['expiry'] <= warnexp:
                ret['expiring'] = True
            if ret['expiry'] <= now:
                ret['expired'] = True
        except BaseException as e:
            self.error(f"Error processing date in certificate: {e}", False)
            ret['certerror'] = True
            return ret

        # SANs
        try:
            ext = cert.extensions.get_extension_for_class(cryptography.x509.SubjectAlternativeName)
            for x in ext.value:
                if isinstance(x, cryptography.x509.DNSName):
                    ret['altnames'].append(x.value.lower().encode('raw_unicode_escape').decode("ascii", errors='replace'))
        except BaseException as e:
            self.debug("Problem processing certificate: " + str(e))
            pass

        certhosts = list()
        try:
            attrs = cert.subject.get_attributes_for_oid(cryptography.x509.oid.NameOID.COMMON_NAME)

            if len(attrs) == 1:
                name = attrs[0].value.lower()
                # CN often duplicates one of the SANs, don't add it then
                if name not in ret['altnames']:
                    certhosts.append(name)
        except BaseException as e:
            self.debug("Problem processing certificate: " + str(e))
            pass

        # Check for mismatch
        if fqdn and ret['issued']:
            fqdn = fqdn.lower()

            try:
                # Extract the CN from the issued section
                if "cn=" + fqdn in ret['issued'].lower():
                    certhosts.append(fqdn)

                # Extract subject alternative names
                for host in ret['altnames']:
                    certhosts.append(host.replace("dns:", ""))

                ret['hosts'] = certhosts

                self.debug("Checking for " + fqdn + " in certificate subject")
                fqdn_tld = ".".join(fqdn.split(".")[1:]).lower()

                found = False
                for chost in certhosts:
                    if chost == fqdn:
                        found = True
                    if chost == "*." + fqdn_tld:
                        found = True
                    if chost == fqdn_tld:
                        found = True

                if not found:
                    ret['mismatch'] = True
            except BaseException as e:
                self.error("Error processing certificate: " + str(e), False)
                ret['certerror'] = True

        return ret

    def extractUrls(self, content):
        """Extract all URLs from a string.

        Args:
            content (str): text to search for URLs

        Returns:
            list: list of identified URLs
        """

        # https://tools.ietf.org/html/rfc3986#section-3.3
        return re.findall(r"(https?://[a-zA-Z0-9-\.:]+/[\-\._~!\$&'\(\)\*\+\,\;=:@/a-zA-Z0-9]*)", html.unescape(content))

    def parseLinks(self, url, data, domains):
        """Find all URLs within the supplied content.

        This does not fetch any URLs!
        A dictionary will be returned, where each link will have the keys
        'source': The URL where the link was obtained from
        'original': What the link looked like in the content it was obtained from
        The key will be the *absolute* URL of the link obtained, so for example if
        the link '/abc' was obtained from 'http://xyz.com', the key in the dict will
        be 'http://xyz.com/abc' with the 'original' attribute set to '/abc'

        Args:
            url (str): TBD
            data (str): data to examine for links
            domains: TBD
        """
        returnLinks = dict()

        if not isinstance(data, str):
            self.debug("parseLinks() data is %s; expected str()" % type(data))
            return returnLinks

        if not data:
            self.debug("parseLinks() called with no data to parse.")
            return returnLinks

        if isinstance(domains, str):
            domains = [domains]

        tags = {
            'a': 'href',
            'img': 'src',
            'script': 'src',
            'link': 'href',
            'area': 'href',
            'base': 'href',
            'form': 'action'
        }

        try:
            proto = url.split(":")[0]
        except BaseException:
            proto = "http"
        if proto is None:
            proto = "http"

        urlsRel = []

        try:
            for t in list(tags.keys()):
                for lnk in BeautifulSoup(data, "lxml", parse_only=SoupStrainer(t)).find_all(t):
                    if lnk.has_attr(tags[t]):
                        urlsRel.append(lnk[tags[t]])
        except BaseException as e:
            self.error("Error parsing with BeautifulSoup: " + str(e), False)
            return returnLinks

        # Loop through all the URLs/links found
        for link in urlsRel:
            if not isinstance(link, str):
                link = str(link)
            link = link.strip()
            linkl = link.lower()
            absLink = None

            if len(link) < 1:
                continue

            # Don't include stuff likely part of some dynamically built incomplete
            # URL found in Javascript code (character is part of some logic)
            if link[len(link) - 1] == '.' or link[0] == '+' or 'javascript:' in linkl or '()' in link:
                self.debug('unlikely link: ' + link)
                continue

            # Filter in-page links
            if re.match('.*#.[^/]+', link):
                self.debug('in-page link: ' + link)
                continue

            # Ignore mail links
            if 'mailto:' in linkl:
                self.debug("Ignoring mail link: " + link)
                continue

            # URL decode links
            if '%2f' in linkl:
                link = urllib.parse.unquote(link)

            # Capture the absolute link:
            # If the link contains ://, it is already an absolute link
            if '://' in link:
                absLink = link

            # If the link starts with a /, the absolute link is off the base URL
            if link.startswith('/'):
                absLink = self.urlBaseUrl(url) + link

            # Protocol relative URLs
            if link.startswith('//'):
                absLink = proto + ':' + link

            # Maybe the domain was just mentioned and not a link, so we make it one
            for domain in domains:
                if absLink is None and domain.lower() in link.lower():
                    absLink = proto + '://' + link

            # Otherwise, it's a flat link within the current directory
            if absLink is None:
                absLink = self.urlBaseDir(url) + link

            # Translate any relative pathing (../)
            absLink = self.urlRelativeToAbsolute(absLink)
            returnLinks[absLink] = {'source': url, 'original': link}

        return returnLinks

    def urlEncodeUnicode(self, url):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), url)

    def getSession(self):
        session = requests.session()
        if self.socksProxy:
            session.proxies = {
                'http': self.socksProxy,
                'https': self.socksProxy,
            }
        return session

    def removeUrlCreds(self, url):
        """Remove key= and others from URLs to avoid credentials in logs."""

        pats = {
            r'key=\S+': "key=XXX",
            r'pass=\S+': "pass=XXX",
            r'user=\S+': "user=XXX",
            r'password=\S+': "password=XXX"
        }

        ret = url
        for pat in pats:
            ret = re.sub(pat, pats[pat], ret, re.IGNORECASE)

        return ret

    def fetchUrl(self, url, fatal=False, cookies=None, timeout=30,
                 useragent="SpiderFoot", headers=None, noLog=False,
                 postData=None, dontMangle=False, sizeLimit=None,
                 headOnly=False, verify=True):
        """Fetch a URL, return the response object."""

        if not url:
            return None

        result = {
            'code': None,
            'status': None,
            'content': None,
            'headers': None,
            'realurl': url
        }

        url = url.strip()

        proxies = dict()
        if self.opts['_socks1type']:
            neverProxyNames = [self.opts['_socks2addr']]
            neverProxySubnets = [
                "127."
                "10.",
                "192.168.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31."
            ]
            host = self.urlFQDN(url)

            # Completely on or off?
            proxy = bool(self.opts['_socks1type'])

            # Never proxy these system/internal locations
            if host in neverProxyNames:
                proxy = False
            for s in neverProxyNames:
                if host.endswith(s):
                    proxy = False
            for sub in neverProxySubnets:
                if host.startswith(sub):
                    proxy = False

            if proxy:
                self.debug(f"Using proxy for {host}")
                self.debug("Proxy set to " + self.opts['_socks2addr'] + ":" + str(self.opts['_socks3port']))
                proxies = {
                    'http': 'socks5h://' + self.opts['_socks2addr'] + ":" + str(self.opts['_socks3port']),
                    'https': 'socks5h://' + self.opts['_socks2addr'] + ":" + str(self.opts['_socks3port'])
                }
            else:
                self.debug("Not using proxy for " + host)

        try:
            header = dict()
            btime = time.time()
            if isinstance(useragent, list):
                header['User-Agent'] = random.SystemRandom().choice(useragent)
            else:
                header['User-Agent'] = useragent

            # Add custom headers
            if headers is not None:
                for k in list(headers.keys()):
                    if isinstance(headers[k], str):
                        header[k] = headers[k]
                    else:
                        header[k] = str(headers[k])

            if sizeLimit or headOnly:
                if not noLog:
                    self.info(f"Fetching (HEAD only): {self.removeUrlCreds(url)} [user-agent: {header['User-Agent']}] [timeout: {timeout}]")

                hdr = self.getSession().head(
                    url,
                    headers=header,
                    proxies=proxies,
                    verify=verify,
                    timeout=timeout
                )
                size = int(hdr.headers.get('content-length', 0))
                newloc = hdr.headers.get('location', url).strip()

                # Relative re-direct
                if newloc.startswith("/") or newloc.startswith("../"):
                    newloc = self.urlBaseUrl(url) + newloc
                result['realurl'] = newloc
                result['code'] = str(hdr.status_code)

                if headOnly:
                    return result

                if size > sizeLimit:
                    return result

                if result['realurl'] != url:
                    if not noLog:
                        self.info(f"Fetching (HEAD only): {self.removeUrlCreds(url)} [user-agent: {header['User-Agent']}] [timeout: {timeout}]")

                    hdr = self.getSession().head(
                        result['realurl'],
                        headers=header,
                        proxies=proxies,
                        verify=verify,
                        timeout=timeout
                    )
                    size = int(hdr.headers.get('content-length', 0))
                    result['realurl'] = hdr.headers.get('location', result['realurl'])
                    result['code'] = str(hdr.status_code)

                    if size > sizeLimit:
                        return result

            if not noLog:
                if cookies is None:
                    self.info(f"Fetching: {self.removeUrlCreds(url)} [user-agent: {header['User-Agent']}] [timeout: {timeout}]")
                else:
                    self.info(f"Fetching (incl. cookies): {self.removeUrlCreds(url)} [user-agent: {header['User-Agent']}] [timeout: {timeout}]")

            try:
                if postData:
                    res = self.getSession().post(
                        url,
                        data=postData,
                        headers=header,
                        proxies=proxies,
                        allow_redirects=True,
                        cookies=cookies,
                        timeout=timeout,
                        verify=verify
                    )
                else:
                    res = self.getSession().get(
                        url,
                        headers=header,
                        proxies=proxies,
                        allow_redirects=True,
                        cookies=cookies,
                        timeout=timeout,
                        verify=verify
                    )
            except requests.exceptions.RequestException:
                raise Exception('Failed to connect to %s' % url) from None

            result['headers'] = dict()
            for header, value in res.headers.items():
                if not isinstance(header, str):
                    header = str(header)

                if not isinstance(value, str):
                    value = str(value)

                result['headers'][header.lower()] = value

            # Sometimes content exceeds the size limit after decompression
            if sizeLimit and len(res.content) > sizeLimit:
                self.debug("Content exceeded size limit, so returning no data just headers")
                result['realurl'] = res.url
                result['code'] = str(res.status_code)
                return result

            if 'refresh' in result['headers']:
                try:
                    newurl = result['headers']['refresh'].split(";url=")[1]
                except BaseException as e:
                    self.debug(f"Refresh header '{result['headers']['refresh']}' found but not parsable: {e}")
                    return result
                self.debug("Refresh header found, re-directing to " + self.removeUrlCreds(newurl))
                return self.fetchUrl(newurl, fatal, cookies, timeout,
                                     useragent, headers, noLog, postData,
                                     dontMangle, sizeLimit, headOnly)

            result['realurl'] = res.url
            result['code'] = str(res.status_code)
            if dontMangle:
                result['content'] = res.content
            else:
                try:
                    result['content'] = res.content.decode("utf-8")
                except UnicodeDecodeError:
                    result['content'] = res.content.decode("ascii")
            if fatal:
                try:
                    res.raise_for_status()
                except requests.exceptions.HTTPError:
                    self.fatal(f"URL could not be fetched ({res.status_code}) / {res.content})")

        except BaseException as e:
            if not noLog:
                # TODO: why another except block?
                try:
                    self.error(f"Unexpected exception ({e}) occurred fetching URL: {url}", False)
                    self.error(traceback.format_exc(), False)
                except BaseException as f:
                    # TODO: why is this exception ignored?
                    self.debug(f"Ignoring exception: {f}")
                    return result
            result['content'] = None
            result['status'] = str(e)
            if fatal:
                self.fatal(f"URL could not be fetched ({e})")

        atime = time.time()
        t = str(atime - btime)
        self.info(f"Fetched {self.removeUrlCreds(url)} ({len(result['content'] or '')} bytes in {t}s)")
        return result

    def checkDnsWildcard(self, target):
        """Check if wildcard DNS is enabled by looking up a random hostname

        Args:
            target (str): TBD
        """

        if not target:
            return False

        randpool = 'bcdfghjklmnpqrstvwxyz3456789'
        randhost = ''.join([random.SystemRandom().choice(randpool) for x in range(10)])

        if not self.resolveHost(randhost + "." + target):
            return False

        return True

    def googleIterate(self, searchString, opts={}):
        """Request search results from the Google API.

        Will return a dict:
        {
          "urls": a list of urls that match the query string,
          "webSearchUrl": url for Google results page,
        }

        Options accepted:
            useragent: User-Agent string to use
            timeout: API call timeout

        Args:
            searchString (str) :TBD
            opts (dict): TBD
        """

        endpoint = "https://www.googleapis.com/customsearch/v1?q={search_string}&".format(
            search_string=searchString.replace(" ", "%20")
        )
        params = {
            "cx": opts["cse_id"],
            "key": opts["api_key"],
        }

        response = self.fetchUrl(
            endpoint + urllib.parse.urlencode(params),
            timeout=opts["timeout"],
        )

        if response['code'] != '200':
            self.error("Failed to get a valid response from the Google API", exception=False)
            return None

        try:
            response_json = json.loads(response['content'])
        except ValueError:
            self.error("The key 'content' in the Google API response doesn't contain valid JSON.", exception=False)
            return None

        if "items" not in response_json:
            return None

        # We attempt to make the URL look as authentically human as possible
        params = {
            "ie": "utf-8",
            "oe": "utf-8",
            "aq": "t",
            "rls": "org.mozilla:en-US:official",
            "client": "firefox-a",
        }
        search_url = "https://www.google.com/search?q={search_string}&{params}".format(
            search_string=searchString.replace(" ", "%20"),
            params=urllib.parse.urlencode(params)
        )
        results = {
            "urls": [str(k['link']) for k in response_json['items']],
            "webSearchUrl": search_url,
        }

        return results

    def bingIterate(self, searchString, opts={}):
        """Request search results from the Bing API.

        Will return a dict:
        {
          "urls": a list of urls that match the query string,
          "webSearchUrl": url for bing results page,
        }

        Options accepted:
            count: number of search results to request from the API
            useragent: User-Agent string to use
            timeout: API call timeout

        Args:
            searchString (str): TBD
            opts (dict): TBD

        """

        endpoint = "https://api.cognitive.microsoft.com/bing/v7.0/search?q={search_string}&".format(
            search_string=searchString.replace(" ", "%20")
        )

        params = {
            "responseFilter": "Webpages",
            "count": opts["count"],
        }

        response = self.fetchUrl(
            endpoint + urllib.parse.urlencode(params),
            timeout=opts["timeout"],
            useragent=opts["useragent"],
            headers={"Ocp-Apim-Subscription-Key": opts["api_key"]},
        )

        if response['code'] != '200':
            self.error("Failed to get a valid response from the bing API", exception=False)
            return None

        try:
            response_json = json.loads(response['content'])
        except ValueError:
            self.error("The key 'content' in the bing API response doesn't contain valid JSON.", exception=False)
            return None

        if ("webPages" in response_json and "value" in response_json["webPages"] and "webSearchUrl" in response_json["webPages"]):
            return {
                "urls": [result["url"] for result in response_json["webPages"]["value"]],
                "webSearchUrl": response_json["webPages"]["webSearchUrl"],
            }

        return None

# end of SpiderFoot class
