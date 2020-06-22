# test_spiderfoot.py
from sflib import SpiderFoot, SpiderFootTarget
import unittest

class TestSpiderFoot(unittest.TestCase):
    """
    Test SpiderFoot
    """

    default_options = {
      '_debug': False,  # Debug
      '__logging': True, # Logging in general
      '__outputfilter': None, # Event types to filter from modules' output
      '__blocknotif': False,  # Block notifications
      '_fatalerrors': False,
      '_useragent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',  # User-Agent to use for HTTP requests
      '_dnsserver': '',  # Override the default resolver
      '_fetchtimeout': 5,  # number of seconds before giving up on a fetch
      '_internettlds': 'https://publicsuffix.org/list/effective_tld_names.dat',
      '_internettlds_cache': 72,
      '__version__': '3.0',
      '__database': 'spiderfoot.db',
      '__webaddr': '127.0.0.1',
      '__webport': 5001,
      '__docroot': '',  # don't put trailing /
      '__modules__': None,  # List of modules. Will be set after start-up.
      '_socks1type': '',
      '_socks2addr': '',
      '_socks3port': '',
      '_socks4user': '',
      '_socks5pwd': '',
      '_socks6dns': True,
      '_torctlport': 9051,
      '__logstdout': False
    }
   
    test_tlds = "// ===BEGIN ICANN DOMAINS===\n\ncom\nnet\norg\n\n// // ===END ICANN DOMAINS===\n"

    def test_init_no_options(self):
        """
        Test __init__(self, options, handle=None):
        """
        sf = SpiderFoot(dict())
        self.assertEqual('TBD', 'TBD')

    def test_init(self):
        """
        Test __init__(self, options, handle=None):
        """
        sf = SpiderFoot(self.default_options)
        self.assertEqual('TBD', 'TBD')

    def test_update_socket(self):
        """
        Test updateSocket(self, sock)
        """
        sf = SpiderFoot(dict())

        sf.updateSocket('new socket')
        self.assertEqual('new socket', sf.socksProxy)

    def test_revert_socket(self):
        """
        Test revertSocket(self)
        """
        sf = SpiderFoot(dict())

        sf.revertSocket()
        self.assertEqual(None, sf.socksProxy)

    def test_refresh_tor_ident_should_return_none(self):
        """
        Test refreshTorIdent(self)
        """
        sf = SpiderFoot(self.default_options)

        res = sf.refreshTorIdent()
        self.assertEqual(None, res)

    def test_opt_value_to_data(self):
        """
        Test optValueToData(self, val, fatal=True, splitLines=True)
        """
        sf = SpiderFoot(self.default_options)

        test_string = "example string"
        opt_data = sf.optValueToData(test_string, fatal=False, splitLines=True)
        self.assertIsInstance(opt_data, str)
        self.assertEqual(test_string, opt_data)

    def test_opt_value_to_data_invalid_opt_should_return_none(self):
        """
        Test optValueToData(self, val, fatal=True, splitLines=True)
        """
        sf = SpiderFoot(self.default_options)

        opt_data = sf.optValueToData(None, fatal=False, splitLines=True)
        self.assertEqual(None, opt_data)

        opt_data = sf.optValueToData([], fatal=False, splitLines=True)
        self.assertEqual(None, opt_data)

    def test_build_graph_data_should_return_a_set(self):
        """
        Test buildGraphData(self, data, flt=list())
        """
        sf = SpiderFoot(dict())

        graph_data = sf.buildGraphData('')
        self.assertIsInstance(graph_data, set)

    def test_build_graph_gexf_should_return_bytes(self):
        """
        Test buildGraphGexf(self, root, title, data, flt=[])
        """
        sf = SpiderFoot(dict())

        gexf = sf.buildGraphGexf('', '', '')
        self.assertIsInstance(gexf, bytes)

    def test_build_graph_json_should_return_a_string(self):
        """
        Test buildGraphJson(self, root, data, flt=list())
        """
        sf = SpiderFoot(dict())

        json = sf.buildGraphJson('', '')
        self.assertIsInstance(json, str)

    def test_set_dbh(self):
        """
        Test setDbh(self, handle)
        """
        sf = SpiderFoot(dict())

        sf.setDbh('new handle')
        self.assertEqual('new handle', sf.dbh)

    def test_set_guid(self):
        """
        Test setGUID(self, uid)
        """
        sf = SpiderFoot(dict())

        sf.setGUID('new guid')
        self.assertEqual('new guid', sf.GUID)

    def test_gen_scan_instance_guid_should_return_a_string(self):
        """
        Test genScanInstanceGUID(self, scanName)
        """
        sf = SpiderFoot(dict())

        scan_instance_id = sf.genScanInstanceGUID(None)
        self.assertIsInstance(scan_instance_id, str)

    def test_dblog_invalid_dbh_should_raise(self):
        """
        Test _dblog(self, level, message, component=None)
        """
        sf = SpiderFoot(self.default_options)

        with self.assertRaises(BaseException) as cm:
            dblog = sf._dblog(None, None, None)

    def test_error(self):
        """
        Test error(self, error, exception=True)
        """
        sf = SpiderFoot(self.default_options)

        sf.error(None, exception=False)
        self.assertEqual('TBD', 'TBD')

        with self.assertRaises(BaseException) as cm:
            sf.error(None, exception=True)

    def test_fatal_should_exit(self):
        """
        Test fatal(self, error)
        """
        sf = SpiderFoot(self.default_options)

        with self.assertRaises(SystemExit) as cm:
            sf.fatal(None)

        self.assertEqual(cm.exception.code, -1)

    def test_status(self):
        """
        Test status(self, message)
        """
        sf = SpiderFoot(self.default_options)

        sf.status(None)
        self.assertEqual('TBD', 'TBD')

    def test_info(self):
        """
        Test info(self, message)
        """
        sf = SpiderFoot(self.default_options)

        sf.info(None)
        self.assertEqual('TBD', 'TBD')

    def test_debug(self):
        """
        Test debug(self, message)
        """
        sf = SpiderFoot(self.default_options)

        sf.debug(None)
        self.assertEqual('TBD', 'TBD')

    def test_my_path_should_return_a_string(self):
        """
        Test myPath(self)
        """
        sf = SpiderFoot(dict())

        path = sf.myPath()
        self.assertIsInstance(path, str)

    def test_data_path_should_return_a_string(self):
        """
        Test def dataPath(self)
        """
        sf = SpiderFoot(dict())

        path = sf.myPath()
        self.assertIsInstance(path, str)

    def test_hash_string_should_return_a_string(self):
        """
        Test hashstring(self, string)
        """
        sf = SpiderFoot(dict())

        hash_string = sf.hashstring('example string')
        self.assertIsInstance(hash_string, str)
        self.assertEqual("aedfb92b3053a21a114f4f301a02a3c6ad5dff504d124dc2cee6117623eec706", hash_string)

    def test_cache_path_should_return_a_string(self):
        """
        Test cachePath(self)
        """
        sf = SpiderFoot(dict())

        cache_path = sf.cachePath()
        self.assertIsInstance(cache_path, str)

    def test_cache_get_should_return_a_string(self):
        """
        Test cachePut(self, label, data)
        Test cacheGet(self, label, timeoutHrs)
        """
        sf = SpiderFoot(dict())

        label = 'test-cache-label'
        data = 'test-cache-data'
        cache_put = sf.cachePut(label, data)
        cache_get = sf.cacheGet(label, sf.opts.get('cacheperiod', 0))
        self.assertIsInstance(cache_get, str)
        self.assertEqual(data, cache_get)

    def test_cache_get_invalid_label_should_return_none(self):
        """
        Test cacheGet(self, label, timeoutHrs)
        """
        sf = SpiderFoot(dict())

        cache_get = sf.cacheGet('', sf.opts.get('cacheperiod', 0))
        self.assertEqual(None, cache_get)

    def test_cache_get_invalid_timeout_should_return_none(self):
        """
        Test cacheGet(self, label, timeoutHrs)
        """
        sf = SpiderFoot(dict())

        cache_get = sf.cacheGet('', None)
        self.assertEqual(None, cache_get)

    def test_config_serialize(self):
        """
        Test configSerialize(self, opts, filterSystem=True)
        """
        self.assertEqual('TBD', 'TBD')

    def test_config_unserialize(self):
        """
        Test configUnserialize(self, opts, referencePoint, filterSystem=True)
        """
        self.assertEqual('TBD', 'TBD')

    def test_target_type(self):
        """
        Test targetType(self, target)
        """
        sf = SpiderFoot(dict())

        target_type = sf.targetType("0.0.0.0")
        self.assertEqual('IP_ADDRESS', target_type)
        target_type = sf.targetType("noreply@spiderfoot.net")
        self.assertEqual('EMAILADDR', target_type)
        target_type = sf.targetType("0.0.0.0/0")
        self.assertEqual('NETBLOCK_OWNER', target_type)
        target_type = sf.targetType("+1234567890")
        self.assertEqual('PHONE_NUMBER', target_type)
        target_type = sf.targetType('"Human Name"')
        self.assertEqual('HUMAN_NAME', target_type)
        target_type = sf.targetType('"abc123"')
        self.assertEqual('USERNAME', target_type)
        target_type = sf.targetType("1234567890")
        self.assertEqual('BGP_AS_OWNER', target_type)
        target_type = sf.targetType("::1")
        self.assertEqual('IPV6_ADDRESS', target_type)
        target_type = sf.targetType("spiderfoot.net")
        self.assertEqual('INTERNET_NAME', target_type)

    def test_target_type_invalid_seed_should_return_none(self):
        """
        Test targetType(self, target)
        """
        sf = SpiderFoot(dict())

        target_type = sf.targetType(None)
        self.assertEqual(None, target_type)

        target_type = sf.targetType("")
        self.assertEqual(None, target_type)

        target_type = sf.targetType('""')
        self.assertEqual(None, target_type)

    def test_modules_producing(self):
        """
        Test modulesProducing(self, events)
        """
        sf = SpiderFoot(dict())

        modules_producing = sf.modulesProducing(list())
        self.assertIsInstance(modules_producing, list)

    def test_modules_consuming(self):
        """
        Test modulesConsuming(self, events)
        """
        sf = SpiderFoot(dict())

        modules_consuming = sf.modulesConsuming(list())
        self.assertIsInstance(modules_consuming, list)

    def test_events_from_modules(self):
        """
        Test eventsFromModules(self, modules)
        """
        sf = SpiderFoot(dict())

        events_from_modules = sf.eventsFromModules(list())
        self.assertIsInstance(events_from_modules, list)

    def test_events_to_modules(self):
        """
        Test eventsToModules(self, modules)
        """
        sf = SpiderFoot(dict())

        events_to_modules = sf.eventsToModules(list())
        self.assertIsInstance(events_to_modules, list)

    def test_url_relative_to_absolute_should_return_a_string(self):
        """
        Test urlRelativeToAbsolute(self, url)
        """
        sf = SpiderFoot(dict())

        relative_url = sf.urlRelativeToAbsolute('/somewhere/else/../../path?param=value#fragment')
        self.assertIsInstance(relative_url, str)
        self.assertEqual('/path?param=value#fragment', relative_url)

    def test_url_base_dir_should_return_a_string(self):
        """
        Test urlBaseDir(self, url)
        """
        sf = SpiderFoot(dict())

        base_dir = sf.urlBaseDir('http://localhost.local/path?param=value#fragment')
        self.assertIsInstance( base_dir, str)
        self.assertEqual('http://localhost.local/', base_dir)

    def test_url_base_url_should_return_a_string(self):
        """
        Test urlBaseUrl(self, url)
        """
        sf = SpiderFoot(dict())

        base_url = sf.urlBaseUrl('http://localhost.local/path?param=value#fragment')
        self.assertIsInstance(base_url, str)
        self.assertEqual('http://localhost.local', base_url)

    def test_url_fqdn_should_return_a_string(self):
        """
        Test urlFQDN(self, url)
        """
        sf = SpiderFoot(dict())

        fqdn = sf.urlFQDN('http://localhost.local')
        self.assertIsInstance(fqdn, str)
        self.assertEqual("localhost.local", fqdn)

    def test_domain_keyword_should_return_a_string(self):
        """
        Test domainKeyword(self, domain, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        keyword = sf.domainKeyword('www.spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(keyword, str)
        self.assertEqual('spiderfoot', keyword)

    def test_domain_keyword_invalid_domain_should_return_none(self):
        """
        Test domainKeyword(self, domain, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        keyword = sf.domainKeyword("", sf.opts.get('_internettlds'))
        self.assertEqual(None, keyword)
        keyword = sf.domainKeyword([], sf.opts.get('_internettlds'))
        self.assertEqual(None, keyword)
        keyword = sf.domainKeyword(None, sf.opts.get('_internettlds'))
        self.assertEqual(None, keyword)

    def test_domain_keywords_should_return_a_set(self):
        """
        Test domainKeywords(self, domainList, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        domain_list = ['www.example.com', 'localhost.local']
        keywords = sf.domainKeywords(domain_list, sf.opts.get('_internettlds'))
        self.assertIsInstance(keywords, set)
        self.assertIn('localhost', keywords)
        self.assertIn('example', keywords)

    def test_domain_keywords_invalid_domainlist_should_return_a_set(self):
        """
        Test domainKeyword(self, domain, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        keywords = sf.domainKeywords("", sf.opts.get('_internettlds'))
        self.assertIsInstance(keywords, set)
        keywords = sf.domainKeywords([], sf.opts.get('_internettlds'))
        self.assertIsInstance(keywords, set)
        keywords = sf.domainKeywords(None, sf.opts.get('_internettlds'))
        self.assertIsInstance(keywords, set)

    def test_host_domain_invalid_host_should_return_none(self):
        """
        Test hostDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        host_domain = sf.hostDomain(None, sf.opts.get('_internettlds'))
        self.assertEqual(None, host_domain)

    def test_host_domain_should_return_a_string(self):
        """
        Test hostDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        host_domain = sf.hostDomain('www.spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(host_domain, str)
        self.assertEqual('spiderfoot.net', host_domain)

        host_domain = sf.hostDomain('spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(host_domain, str)
        self.assertEqual('spiderfoot.net', host_domain)

        host_domain = sf.hostDomain('abc.www.spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(host_domain, str)
        self.assertEqual('spiderfoot.net', host_domain)

    def test_host_domain_invalid_tldlist_should_return_none(self):
        """
        Test hostDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(dict())

        host_domain = sf.hostDomain('spiderfoot.net', None)
        self.assertEqual(None, host_domain)

    def test_is_domain_should_return_a_boolean(self):
        """
        Test isDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        is_domain = sf.isDomain('spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(is_domain, bool)
        self.assertTrue(is_domain)

    def test_is_domain_invalid_tldlist_should_return_false(self):
        """
        Test isDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)

        is_domain = sf.isDomain('spiderfoot.net', None)
        self.assertIsInstance(is_domain, bool)
        self.assertFalse(is_domain)

    def test_is_domain_invalid_tld_should_return_false(self):
        """
        Test isDomain(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        is_domain = sf.isDomain('spiderfoot.not_a_tld', sf.opts.get('_internettlds'))
        self.assertIsInstance(is_domain, bool)
        self.assertFalse(is_domain)

    def test_valid_host_invalid_tldlist_should_return_false(self):
        """
        Test validHost(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)

        is_host = sf.validHost('spiderfoot.net', None)
        self.assertIsInstance(is_host, bool)
        self.assertFalse(is_host)

    def test_valid_host_valid_host_should_return_true(self):
        """
        Test validHost(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        is_host = sf.validHost('spiderfoot.net', sf.opts.get('_internettlds'))
        self.assertIsInstance(is_host, bool)
        self.assertTrue(is_host)

    def test_valid_host_invalid_host_should_return_false(self):
        """
        Test validHost(self, hostname, tldList)
        """
        sf = SpiderFoot(self.default_options)
        sf.opts['_internettlds'] = self.test_tlds

        is_valid = sf.validHost('something.gif', sf.opts.get('_internettlds'))
        self.assertIsInstance(is_valid, bool)
        self.assertFalse(is_valid)

    def test_valid_ip_should_return_a_boolean(self):
        """
        Test validIP(self, address)
        """
        sf = SpiderFoot(dict())

        valid_ip = sf.validIP('0.0.0.0')
        self.assertIsInstance(valid_ip, bool)
        self.assertTrue(valid_ip)

    def test_valid_ip6_should_return_a_boolean(self):
        """
        Test validIP6(self, address)
        """
        sf = SpiderFoot(dict())

        valid_ip6 = sf.validIP6('::1')
        self.assertIsInstance(valid_ip6, bool)
        self.assertTrue(valid_ip6)

    def test_valid_ip_network_should_return_a_boolean(self):
        """
        Test validIpNetwork(self, cidr)
        """
        sf = SpiderFoot(dict())

        valid_ip_network = sf.validIpNetwork('0.0.0.0/0')
        self.assertIsInstance(valid_ip_network, bool)

    def test_valid_email_should_return_a_boolean(self):
        """
        Test validEmail(self, email)
        """
        sf = SpiderFoot(dict())

        valid_email = sf.validEmail(None)
        self.assertIsInstance(valid_email, bool)
        self.assertFalse(valid_email)

        valid_email = sf.validEmail([])
        self.assertIsInstance(valid_email, bool)
        self.assertFalse(valid_email)

        valid_email = sf.validEmail('root@localhost')
        self.assertIsInstance(valid_email, bool)
        self.assertFalse(valid_email)

        valid_email = sf.validEmail('root@localhost.local')
        self.assertIsInstance(valid_email, bool)
        self.assertTrue(valid_email)

    def test_normalize_dns(self):
        """
        Test normalizeDNS(self, res)
        """
        sf = SpiderFoot(self.default_options)

        dns = sf.normalizeDNS(["example.local.", ["spiderfoot.net."]])
        self.assertIsInstance(dns, list)
        self.assertIn("example.local", dns)
        self.assertIn("spiderfoot.net", dns)

    def test_normalize_dns_should_return_list(self):
        """
        Test normalizeDNS(self, res)
        """
        sf = SpiderFoot(self.default_options)

        dns = sf.normalizeDNS(None)
        self.assertIsInstance(dns, list)

        dns = sf.normalizeDNS([])
        self.assertIsInstance(dns, list)

    def test_sanitise_input(self):
        """
        Test sanitiseInput(self, cmd)
        """
        sf = SpiderFoot(dict())

        safe = sf.sanitiseInput("example-string")
        self.assertIsInstance(safe, bool)
        self.assertTrue(safe)

        safe = sf.sanitiseInput("example-string\n")
        self.assertIsInstance(safe, bool)
        self.assertFalse(safe)

        safe = sf.sanitiseInput("example string")
        self.assertIsInstance(safe, bool)
        self.assertFalse(safe)

        safe = sf.sanitiseInput("-example string")
        self.assertIsInstance(safe, bool)
        self.assertFalse(safe)

        safe = sf.sanitiseInput(".. example string")
        self.assertIsInstance(safe, bool)
        self.assertFalse(safe)

    def test_dictwords_should_return_a_list(self):
        """
        Test dictwords(self)
        """
        sf = SpiderFoot(dict())

        dict_words = sf.dictwords()
        self.assertIsInstance(dict_words, list)

    def test_dictnames_should_return_a_list(self):
        """
        Test dictnames(self)
        """
        sf = SpiderFoot(dict())

        dict_names = sf.dictnames()
        self.assertIsInstance(dict_names, list)

    def test_data_parent_child_to_tree_should_return_dict(self):
        """
        Test dataParentChildToTree(self, data)
        """
        sf = SpiderFoot(self.default_options)

        tree = sf.dataParentChildToTree(None)
        self.assertIsInstance(tree, dict)

        tree = sf.dataParentChildToTree([])
        self.assertIsInstance(tree, dict)

        tree = sf.dataParentChildToTree("")
        self.assertIsInstance(tree, dict)

        tree = sf.dataParentChildToTree(dict())
        self.assertIsInstance(tree, dict)

    def test_resolve_host_should_return_list(self):
        """
        Test resolveHost(self, host)
        """
        sf = SpiderFoot(self.default_options)

        addrs = sf.resolveHost('one.one.one.one')
        self.assertIsInstance(addrs, list)
        self.assertTrue(addrs)
        self.assertIn('1.1.1.1', addrs)

        addrs = sf.resolveHost(None)
        self.assertFalse(addrs)
        self.assertIsInstance(addrs, list)

    def test_resolve_ip_should_return_list(self):
        """
        Test resolveIP(self, ipaddr)
        """
        sf = SpiderFoot(self.default_options)

        addrs = sf.resolveIP('1.1.1.1')
        self.assertIsInstance(addrs, list)
        self.assertTrue(addrs)
        self.assertIn('one.one.one.one', addrs)

        addrs = sf.resolveIP('2606:4700:4700::1001')
        self.assertIsInstance(addrs, list)
        self.assertTrue(addrs)
        self.assertIn('one.one.one.one', addrs)

        addrs = sf.resolveIP(None)
        self.assertFalse(addrs)
        self.assertIsInstance(addrs, list)

        addrs = sf.resolveIP([])
        self.assertFalse(addrs)
        self.assertIsInstance(addrs, list)

        addrs = sf.resolveIP("")
        self.assertFalse(addrs)
        self.assertIsInstance(addrs, list)

    def test_resolve_host6_should_return_a_list(self):
        """
        Test resolveHost6(self, hostname)
        """
        sf = SpiderFoot(self.default_options)

        addrs = sf.resolveHost6('one.one.one.one')
        self.assertIsInstance(addrs, list)
        self.assertTrue(addrs)
        self.assertIn('2606:4700:4700::1001', addrs)
        self.assertIn('2606:4700:4700::1111', addrs)

        addrs = sf.resolveHost6(None)
        self.assertFalse(addrs)
        self.assertIsInstance(addrs, list)

    def test_validate_ip_should_return_bool(self):
        """
        Test validateIP(self, host, ip)
        """
        sf = SpiderFoot(self.default_options)

        validate_ip = sf.validateIP(None, None)
        self.assertIsInstance(validate_ip, bool)
        self.assertEqual(False, validate_ip)

        self.assertEqual('TBD', 'TBD')

    def test_resolve_targets_should_return_list(self):
        """
        Test resolveTargets(self, target, validateReverse)
        """
        sf = SpiderFoot(self.default_options)

        target = SpiderFootTarget("spiderfoot.net", "INTERNET_NAME")
        resolve_targets = sf.resolveTargets(target, False)
        self.assertIsInstance(resolve_targets, list)
        self.assertIn('spiderfoot.net', resolve_targets)

    def test_safe_socket(self):
        """
        Test safeSocket(self, host, port, timeout)
        """
        sf = SpiderFoot(self.default_options)

        self.assertEqual('TBD', 'TBD')

    def test_safe_ssl_socket(self):
        """
        Test safeSSLSocket(self, host, port, timeout)
        """
        sf = SpiderFoot(self.default_options)

        self.assertEqual('TBD', 'TBD')

    def test_parse_robots_txt_should_return_list(self):
        """
        Test parseRobotsTxt(self, robotsTxtData)
        """
        sf = SpiderFoot(self.default_options)

        robots_txt = sf.parseRobotsTxt(None)
        self.assertIsInstance(robots_txt, list)

        robots_txt = sf.parseRobotsTxt("")
        self.assertIsInstance(robots_txt, list)

        robots_txt = sf.parseRobotsTxt([])
        self.assertIsInstance(robots_txt, list)

        robots_txt = sf.parseRobotsTxt("disallow:")
        self.assertIsInstance(robots_txt, list)
        self.assertFalse(robots_txt)

        robots_txt = sf.parseRobotsTxt("disallow: /disallowed/path\n")
        self.assertIsInstance(robots_txt, list)
        self.assertIn("/disallowed/path", robots_txt)

    def test_parse_emails_should_return_list(self):
        """
        Test parseEmails(self, data)
        """
        sf = SpiderFoot(self.default_options)

        parse_emails = sf.parseEmails("<html><body><p>From:noreply@spiderfoot.net</p><p>Subject:Hello user@spiderfoot.net, here's some text</p></body></html>")
        self.assertIsInstance(parse_emails, list)
        self.assertIn('noreply@spiderfoot.net', parse_emails)
        self.assertIn('user@spiderfoot.net', parse_emails)

    def test_parse_emails_invalid_data_should_return_list(self):
        """
        Test parseEmails(self, data)
        """
        sf = SpiderFoot(self.default_options)

        parse_emails = sf.parseEmails(None)
        self.assertIsInstance(parse_emails, list)

    def test_ssl_der_to_pem(self):
        """
        Test sslDerToPem(self, der)
        """
        sf = SpiderFoot(self.default_options)

        self.assertEqual('TBD', 'TBD')

    def test_ssl_der_to_pem_invalid_cert_should_return_none(self):
        """
        Test sslDerToPem(self, der)
        """
        sf = SpiderFoot(self.default_options)

        with self.assertRaises(TypeError) as cm:
            pem = sf.sslDerToPem(None)

        with self.assertRaises(TypeError) as cm:
            pem = sf.sslDerToPem([])

        with self.assertRaises(TypeError) as cm:
            pem = sf.sslDerToPem("")

    def test_parse_cert_should_return_a_dict(self):
        """
        Test parseCert(self, rawcert, fqdn=None, expiringdays=30)
        """
        sf = SpiderFoot(self.default_options)

        parse_cert = sf.parseCert("-----BEGIN CERTIFICATE-----\nMIIEkjCCA3qgAwIBAgIQCgFBQgAAAVOFc2oLheynCDANBgkqhkiG9w0BAQsFADA/MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMTDkRTVCBSb290IENBIFgzMB4XDTE2MDMxNzE2NDA0NloXDTIxMDMxNzE2NDA0NlowSjELMAkGA1UEBhMCVVMxFjAUBgNVBAoTDUxldCdzIEVuY3J5cHQxIzAhBgNVBAMTGkxldCdzIEVuY3J5cHQgQXV0aG9yaXR5IFgzMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnNMM8FrlLke3cl03g7NoYzDq1zUmGSXhvb418XCSL7e4S0EFq6meNQhY7LEqxGiHC6PjdeTm86dicbp5gWAf15Gan/PQeGdxyGkOlZHP/uaZ6WA8SMx+yk13EiSdRxta67nsHjcAHJyse6cF6s5K671B5TaYucv9bTyWaN8jKkKQDIZ0Z8h/pZq4UmEUEz9l6YKHy9v6Dlb2honzhT+Xhq+w3Brvaw2VFn3EK6BlspkENnWAa6xK8xuQSXgvopZPKiAlKQTGdMDQMc2PMTiVFrqoM7hD8bEfwzB/onkxEz0tNvjj/PIzark5McWvxI0NHWQWM6r6hCm21AvA2H3DkwIDAQABo4IBfTCCAXkwEgYDVR0TAQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8EBAMCAYYwfwYIKwYBBQUHAQEEczBxMDIGCCsGAQUFBzABhiZodHRwOi8vaXNyZy50cnVzdGlkLm9jc3AuaWRlbnRydXN0LmNvbTA7BggrBgEFBQcwAoYvaHR0cDovL2FwcHMuaWRlbnRydXN0LmNvbS9yb290cy9kc3Ryb290Y2F4My5wN2MwHwYDVR0jBBgwFoAUxKexpHsscfrb4UuQdf/EFWCFiRAwVAYDVR0gBE0wSzAIBgZngQwBAgEwPwYLKwYBBAGC3xMBAQEwMDAuBggrBgEFBQcCARYiaHR0cDovL2Nwcy5yb290LXgxLmxldHNlbmNyeXB0Lm9yZzA8BgNVHR8ENTAzMDGgL6AthitodHRwOi8vY3JsLmlkZW50cnVzdC5jb20vRFNUUk9PVENBWDNDUkwuY3JsMB0GA1UdDgQWBBSoSmpjBH3duubRObemRWXv86jsoTANBgkqhkiG9w0BAQsFAAOCAQEA3TPXEfNjWDjdGBX7CVW+dla5cEilaUcne8IkCJLxWh9KEik3JHRRHGJouM2VcGfl96S8TihRzZvoroed6ti6WqEBmtzw3Wodatg+VyOeph4EYpr/1wXKtx8/wApIvJSwtmVi4MFU5aMqrSDE6ea73Mj2tcMyo5jMd6jmeWUHK8so/joWUoHOUgwuX4Po1QYz+3dszkDqMp4fklxBwXRsW10KXzPMTZ+sOPAveyxindmjkW8lGy+QsRlGPfZ+G6Z6h7mjem0Y+iWlkYcV4PIWL1iwBi8saCbGS5jN2p8M+X+Q7UNKEkROb3N6KOqkqm57TH2H3eDJAkSnh6/DNFu0Qg==\n-----END CERTIFICATE-----")
        self.assertIsInstance(parse_cert, dict)

    def test_parse_cert_invalid_cert_should_return_none(self):
        """
        Test parseCert(self, rawcert, fqdn=None, expiringdays=30)
        """
        sf = SpiderFoot(self.default_options)

        parse_cert = sf.parseCert(None, 'spiderfoot.net', 30)
        self.assertEqual(None, parse_cert)

    def test_parse_cert_invalid_fqdn_should_return_none(self):
        """
        Test parseCert(self, rawcert, fqdn=None, expiringdays=30)
        """
        sf = SpiderFoot(self.default_options)

        parse_cert = sf.parseCert(None, None, 30)
        self.assertEqual(None, parse_cert)

    def test_parse_cert_invalid_expiringdays_should_return_none(self):
        """
        Test parseCert(self, rawcert, fqdn=None, expiringdays=30)
        """
        sf = SpiderFoot(self.default_options)

        parse_cert = sf.parseCert(None, 'spiderfoot.net', None)
        self.assertEqual(None, parse_cert)

    def test_parse_links_should_return_a_dict(self):
        """
        Test parseLinks(self, url, data, domains)
        """
        sf = SpiderFoot(self.default_options)

        parse_links = sf.parseLinks('url', 'example html content', 'domains')
        self.assertIsInstance(parse_links, dict)

    def test_parse_links_invalid_url_should_return_a_dict(self):
        """
        Test parseLinks(self, url, data, domains)
        """
        sf = SpiderFoot(self.default_options)

        parse_links = sf.parseLinks(None, 'example html content', 'domains')
        self.assertIsInstance(parse_links, dict)

    def test_parse_links_invalid_data_should_return_a_dict(self):
        """
        Test parseLinks(self, url, data, domains)
        """
        sf = SpiderFoot(self.default_options)

        parse_links = sf.parseLinks('url', None, 'domains')
        self.assertIsInstance(parse_links, dict)

    def test_parse_links_invalid_domains_should_return_a_dict(self):
        """
        Test parseLinks(self, url, data, domains)
        """
        sf = SpiderFoot(self.default_options)

        parse_links = sf.parseLinks('url', 'example html content', None)
        self.assertEqual(dict, type(parse_links))

    def test_url_encode_unicode_should_return_a_string(self):
        """
        Test urlEncodeUnicode(self, url)
        """
        sf = SpiderFoot(self.default_options)

        url_encode_unicode = sf.urlEncodeUnicode('url')
        self.assertIsInstance(url_encode_unicode, str)

    def test_fetch_url(self):
        """
        Test fetchUrl(self, url, fatal=False, cookies=None, timeout=30,
                 useragent="SpiderFoot", headers=None, noLog=False,
                 postData=None, dontMangle=False, sizeLimit=None,
                 headOnly=False, verify=False)
        """
        self.assertEqual('TBD', 'TBD')

    def test_fetch_url_invalid_url_should_return_none(self):
        """
        Test fetchUrl(self, url, fatal=False, cookies=None, timeout=30,
                 useragent="SpiderFoot", headers=None, noLog=False,
                 postData=None, dontMangle=False, sizeLimit=None,
                 headOnly=False, verify=False)
        """
        sf = SpiderFoot(self.default_options)

        res = sf.fetchUrl(None)
        self.assertEqual(None, res)

    def test_check_dns_wildcard_invalid_target_should_return_none(self):
        """
        Test checkDnsWildcard(self, target)
        """
        sf = SpiderFoot(self.default_options)

        check_dns_wildcard = sf.checkDnsWildcard(None)
        self.assertIsInstance(check_dns_wildcard, bool)

    def test_check_dns_wildcard_should_return_a_boolean(self):
        """
        Test checkDnsWildcard(self, target)
        """
        sf = SpiderFoot(self.default_options)

        check_dns_wildcard = sf.checkDnsWildcard('local')
        self.assertIsInstance(check_dns_wildcard, bool)

    def test_google_iterate(self):
        """
        Test googleIterate(self, searchString, opts=dict())
        """
        self.assertEqual('TBD', 'TBD')

    def test_bing_iterate(self):
        """
        Test bingIterate(self, searchString, opts=dict())
        """
        self.assertEqual('TBD', 'TBD')

if __name__ == '__main__':
    unittest.main()

