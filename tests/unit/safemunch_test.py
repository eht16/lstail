# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from lstail.util.safe_munch import DefaultSafeMunch, safe_munchify, SafeMunch
from tests.base import BaseTestCase


# Most of the tests are taken from Munch (https://github.com/Infinidat/munch)
# and ported to Unittest.


class SafeMunchTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def test_base(self):
        smunch = SafeMunch()
        smunch.hello = 'world'
        self.assertEqual(smunch.hello, 'world')
        smunch['hello'] += "!"
        self.assertEqual(smunch.hello, 'world!')
        smunch.foo = SafeMunch(lol=True)
        self.assertTrue(smunch.foo.lol)
        self.assertIs(smunch.foo, smunch['foo'])

        self.assertEqual(sorted(smunch.keys()), ['foo', 'hello'])

        smunch.sm_dict_update({'ponies': 'are pretty!'}, hello=42)
        expected_dict = SafeMunch(
            {'ponies': 'are pretty!',
             'foo': SafeMunch({'lol': True}),
             'hello': 42})
        self.assertEqual(smunch, expected_dict)

        test_list = sorted([(k, smunch[k]) for k in smunch])
        expected_list = [
            ('foo', SafeMunch({'lol': True})),
            ('hello', 42),
            ('ponies', 'are pretty!')]
        self.assertEqual(test_list, expected_list)

        test_string = "The {knights} who say {ni}!".format(
            **SafeMunch(knights='lolcats', ni='can haz'))
        expected_string = 'The lolcats who say can haz!'
        self.assertEqual(test_string, expected_string)

    # ----------------------------------------------------------------------
    def test_contains(self):
        smunch = SafeMunch(ponies='are pretty!')
        self.assertIn('ponies', smunch)
        self.assertFalse(('foo' in smunch))

        smunch['foo'] = 42
        self.assertIn('foo', smunch)

        smunch.hello = 'hai'
        self.assertIn('hello', smunch)

        smunch[None] = 123
        self.assertIn(None, smunch)

        smunch[False] = 456
        self.assertIn(False, smunch)

    # ----------------------------------------------------------------------
    def test_getattr(self):
        smunch = SafeMunch(bar='baz', lol={})

        with self.assertRaises(AttributeError):
            smunch.foo  # pylint: disable=pointless-statement

        self.assertEqual(smunch.bar, 'baz')
        self.assertEqual(getattr(smunch, 'bar'), 'baz')
        self.assertEqual(smunch['bar'], 'baz')
        self.assertIs(smunch.lol, smunch['lol'])
        self.assertIs(smunch.lol, getattr(smunch, 'lol'))

    # ----------------------------------------------------------------------
    def test_setattr(self):
        smunch = SafeMunch(foo='bar', this_is='useful when subclassing')

        smunch.values = 'uh oh'
        self.assertEqual(smunch.values, 'uh oh')

        # SafeMunch doesn't have a .values() method
        self.assertFalse(hasattr(smunch.values, '__call__'))

    # ----------------------------------------------------------------------
    def test_setattr_munchify(self):
        smunch = SafeMunch()
        smunch.lvl1 = {'lvl2': {'lvl3': 'yay'}}
        self.assertEqual(smunch.lvl1.lvl2.lvl3, 'yay')  # pylint: disable=no-member

    # ----------------------------------------------------------------------
    def test_delattr(self):
        smunch = SafeMunch(lol=42)
        del smunch.lol

        with self.assertRaises(KeyError):
            smunch['lol']  # pylint: disable=pointless-statement

        with self.assertRaises(AttributeError):
            smunch.lol  # pylint: disable=pointless-statement

    # ----------------------------------------------------------------------
    def test_repr(self):
        smunch = SafeMunch(foo=SafeMunch(lol=True), hello=42, ponies='are pretty!')
        self.assertTrue(repr(smunch).startswith("SafeMunch({'"))
        self.assertIn("'ponies': 'are pretty!'", repr(smunch))
        self.assertIn("'hello': 42", repr(smunch))
        self.assertIn("'foo': SafeMunch({'lol': True})", repr(smunch))
        self.assertIn("'hello': 42", repr(smunch))

        with_spaces = SafeMunch({1: 2, 'a b': 9, 'c': SafeMunch({'simple': 5})})
        self.assertTrue(repr(with_spaces).startswith("SafeMunch({"))
        self.assertIn("'a b': 9", repr(with_spaces))
        self.assertIn("1: 2", repr(with_spaces))
        self.assertIn("'c': SafeMunch({'simple': 5})", repr(with_spaces))
        sm_repr = SafeMunch({'a b': 9, 1: 2, 'c': SafeMunch({'simple': 5})})
        self.assertEqual(eval(repr(with_spaces)), sm_repr)  # pylint: disable=eval-used

    # ----------------------------------------------------------------------
    def test_reserved_attributes(self):
        # Make sure that the default attributes on the Munch instance are
        # accessible.
        for attrname in dir(SafeMunch):
            self._test_reserved_attribute(attrname)

    # ----------------------------------------------------------------------
    def _test_reserved_attribute(self, attrname):
        taken_munch = SafeMunch(**{attrname: 'abc123'})
        msg = 'attribute: {}'.format(attrname)

        # Make sure that the attribute is determined as in the filled collection...
        self.assertIn(attrname, taken_munch, msg=msg)

        # ...and that it is available using key access...
        self.assertEqual(taken_munch[attrname], 'abc123', msg=msg)

        # ...but that it is not available using attribute access.
        attr = getattr(taken_munch, attrname)
        self.assertNotEqual(attr, 'abc123', msg=msg)

        # Make sure that the attribute is not seen contained in the empty collection...
        empty_munch = SafeMunch()
        self.assertNotIn(attrname, empty_munch, msg=msg)

        # ...and that the attr is of the correct original type.
        attr = getattr(empty_munch, attrname)
        if attrname == '__doc__':
            self.assertIsInstance(attr, str, msg=msg)
        elif attrname == '__module__':
            self.assertIn('safe_munch', attr, msg=msg)
        elif attrname == '__dict__':
            self.assertEqual(attr, {}, msg=msg)
        elif attrname == '__weakref__':
            self.assertIsNone(attr, msg=msg)
        elif attrname == '__hash__':
            self.assertIsNone(attr, msg=msg)
        else:
            self.assertTrue(callable(attr), msg=msg)

    # ----------------------------------------------------------------------
    def test_munchify(self):
        smunch = safe_munchify({'urmom': {'sez': {'what': 'what'}}})
        self.assertEqual(smunch.urmom.sez.what, 'what')

        smunch = safe_munchify(
            {'lol': ('cats', {'hah': 'i win again'}),
             'hello': [{'french': 'salut', 'german': 'hallo'}]})
        self.assertEqual(smunch.hello[0].french, 'salut')
        self.assertEqual(smunch.lol[1].hah, 'i win again')

    # ----------------------------------------------------------------------
    def test_sm_dict_keys_flattened(self):
        test_data = {
            'lol': 'yay',
            'urmom': {'sez': {'what': 'what'}},
            'cats': {'hah': 'i win again', 'abc': '123'}}

        smunch = safe_munchify(test_data)
        flattened_keys = smunch.sm_dict_keys_flattened(separator='-')
        sorted_flattened_keys = sorted(flattened_keys)
        expected_keys = ['cats-abc', 'cats-hah', 'lol', 'urmom-sez-what']
        self.assertEqual(sorted_flattened_keys, expected_keys)

        test_data['keys_test'] = {'keys': 'possible to set but not to get'}
        smunch = safe_munchify(test_data)
        flattened_keys = smunch.sm_dict_keys_flattened(data=dict(smunch), separator='.')
        sorted_flattened_keys = sorted(flattened_keys)
        expected_keys = ['cats.abc', 'cats.hah', 'keys_test.keys', 'lol', 'urmom.sez.what']
        self.assertEqual(sorted_flattened_keys, expected_keys)

    # ----------------------------------------------------------------------
    def test_special_key_keys(self):
        # key "keys" is special:
        # "keys" is a method on SafeMunch (necessary to use ** magic)
        # you can set and get it as a key using __setitem__ and __getitem__ but cannot query the key
        # using __getattr__ as this should return the method callable
        smunch = SafeMunch()

        # set "keys" as item
        smunch['keys'] = 'values'
        self.assertIn('keys', smunch)

        # get "keys" as item
        value = smunch['keys']
        self.assertEqual(value, 'values')

        # get as attribute and get the "keys" method
        value = smunch.keys
        self.assertEqual(smunch.keys, value)

    # ----------------------------------------------------------------------
    def test_getattr_default(self):
        smunch = DefaultSafeMunch(bar='baz', lol={})
        self.assertIsNone(smunch.foo)
        self.assertIsNone(smunch['foo'])

        self.assertEqual(smunch.bar, 'baz')
        self.assertEqual(getattr(smunch, 'bar'), 'baz')
        self.assertEqual(smunch['bar'], 'baz')
        self.assertIs(smunch.lol, smunch['lol'])
        self.assertIs(smunch.lol, getattr(smunch, 'lol'))

        undefined = object()
        smunch = DefaultSafeMunch(undefined, bar='baz', lol={})
        self.assertIs(smunch.foo, undefined)
        self.assertIs(smunch['foo'], undefined)

    # ----------------------------------------------------------------------
    def test_setattr_default(self):
        smunch = DefaultSafeMunch(foo='bar', this_is='useful when subclassing')

        smunch.values = 'uh oh'
        self.assertEqual(smunch.values, 'uh oh')
        self.assertIsNotNone(smunch['values'])

        smunch.keys = 'uh oh'
        self.assertEqual(smunch.keys, 'uh oh')
        self.assertIsNone(smunch['keys'])

        self.assertIsNone(smunch.__default__)
        self.assertNotIn('__default__', smunch)

    # ----------------------------------------------------------------------
    def test_delattr_default(self):
        smunch = DefaultSafeMunch(lol=42)
        del smunch.lol

        self.assertIsNone(smunch.lol)
        self.assertIsNone(smunch['lol'])

    # ----------------------------------------------------------------------
    def test_munchify_default(self):
        undefined = object()
        smunch = safe_munchify(
            {'urmom': {'sez': {'whatk': 'whatv'}}},
            factory=DefaultSafeMunch,
            default=undefined)
        self.assertEqual(smunch.urmom.sez.whatk, 'whatv')
        self.assertIs(smunch.urdad, undefined)
        self.assertIs(smunch.urmom.sez.ni, undefined)

    # ----------------------------------------------------------------------
    def test_repr_default(self):
        smunch = DefaultSafeMunch(foo=DefaultSafeMunch(lol=True), ponies='are pretty!')
        self.assertTrue(repr(smunch).startswith("DefaultSafeMunch(None, {'"))
        self.assertIn("'ponies': 'are pretty!'", repr(smunch))

    # ----------------------------------------------------------------------
    def test_sm_dict_keys_flattened_default(self):
        test_data = {
            'lol': 'yay',
            'urmom': {'sez': {'what': 'what'}},
            'cats': {'hah': 'i win again', 'abc': '123'}}

        undefined = object()
        smunch = safe_munchify(test_data, factory=DefaultSafeMunch, default=undefined)
        flattened_keys = smunch.sm_dict_keys_flattened(separator='-')
        sorted_flattened_keys = sorted(flattened_keys)
        expected_keys = ['cats-abc', 'cats-hah', 'lol', 'urmom-sez-what']
        self.assertEqual(sorted_flattened_keys, expected_keys)

        test_data['keys_test'] = {'keys': 'possible to set but not to get'}
        smunch = safe_munchify(test_data, factory=DefaultSafeMunch, default=undefined)
        flattened_keys = smunch.sm_dict_keys_flattened(data=dict(smunch), separator='.')
        sorted_flattened_keys = sorted(flattened_keys)
        expected_keys = ['cats.abc', 'cats.hah', 'keys_test.keys', 'lol', 'urmom.sez.what']
        self.assertEqual(sorted_flattened_keys, expected_keys)
