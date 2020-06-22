# test_spiderfoottarget.py
from sflib import SpiderFootTarget
import unittest

class TestSpiderFootTarget(unittest.TestCase):
    """
    Test SpiderFootTarget
    """

    valid_target_types = [
        'IP_ADDRESS', 'IPV6_ADDRESS', 'NETBLOCK_OWNER', 'INTERNET_NAME',
        'EMAILADDR', 'HUMAN_NAME', 'BGP_AS_OWNER', 'PHONE_NUMBER', "USERNAME"
    ]

    def test_init_unsupported_target_type_should_raise(self):
        """
        Test __init__(self, targetValue, typeName)
        """
        target_value = 'example target value'

        with self.assertRaises(ValueError) as cm:
            target_type = 'example target type'
            target = SpiderFootTarget(target_value, target_type)

    def test_init_supported_target_types(self):
        """
        Test __init__(self, targetValue, typeName)
        """
        target_value = 'example target value'

        for target_type in self.valid_target_types:
            with self.subTest(target_type=target_type):
                target = SpiderFootTarget(target_value, target_type)
                self.assertEqual(SpiderFootTarget, type(target))
                self.assertEqual(target.getType(), target_type)
                self.assertEqual(target.getValue(), target_value)

    def test_set_alias(self):
        """
        Test setAlias(self, value, typeName)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        set_alias = target.setAlias(None, None)
        self.assertEqual('TBD', 'TBD')

    def test_get_aliases_should_return_a_list(self):
        """
        Test getAliases(self)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        aliases = target.getAliases()
        self.assertEqual(list, type(aliases))

    def test_get_equivalents_should_return_a_list(self):
        """
        Test _getEquivalents(self, typeName)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        equivalents = target._getEquivalents(target_type)
        self.assertEqual(list, type(equivalents))

    def test_get_names_should_return_a_list(self):
        """
        Test getNames(self)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        names = target.getNames()
        self.assertEqual(list, type(names))

    def test_get_addresses_should_return_a_list(self):
        """
        Test getAddresses(self)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        addresses = target.getAddresses()
        self.assertEqual(list, type(addresses))

    def test_matches_should_return_a_boolean(self):
        """
        Test matches(self, value, includeParents=False, includeChildren=True)
        """
        target_value = 'example target value'
        target_type = 'IP_ADDRESS'
        target = SpiderFootTarget(target_value, target_type)

        matches = target.matches(None)
        self.assertEqual(bool, type(matches))

if __name__ == '__main__':
    unittest.main()

