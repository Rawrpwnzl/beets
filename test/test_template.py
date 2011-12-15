# This file is part of beets.
# Copyright 2011, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Tests for template engine.
"""
import unittest

import _common
from beets.util import functemplate

def _normexpr(expr):
    """Normalize an Expression object's parts, collapsing multiple
    adjacent text blocks and removing empty text blocks. Generates a
    sequence of parts.
    """
    textbuf = []
    for part in expr.parts:
        if isinstance(part, basestring):
            textbuf.append(part)
        else:
            if textbuf:
                text = u''.join(textbuf)
                if text:
                    yield text
                    textbuf = []
            yield part
    if textbuf:
        text = u''.join(textbuf)
        if text:
            yield text

def _normparse(text):
    """Parse a template and then normalize the resulting Expression."""
    return _normexpr(functemplate._parse(text))

class ParseTest(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(list(_normparse(u'')), [])

    def _assert_symbol(self, obj, ident):
        """Assert that an object is a Symbol with the given identifier.
        """
        self.assertTrue(isinstance(obj, functemplate.Symbol),
                        u"not a Symbol: %s" % repr(obj))
        self.assertEqual(obj.ident, ident,
                         u"wrong identifier: %s vs. %s" %
                         (repr(obj.ident), repr(ident)))

    def _assert_call(self, obj, ident, numargs):
        """Assert that an object is a Call with the given identifier and
        argument count.
        """
        self.assertTrue(isinstance(obj, functemplate.Call),
                        u"not a Call: %s" % repr(obj))
        self.assertEqual(obj.ident, ident,
                         u"wrong identifier: %s vs. %s" %
                         (repr(obj.ident), repr(ident)))
        self.assertEqual(len(obj.args), numargs,
                         u"wrong argument count in %s: %i vs. %i" %
                         (repr(obj.ident), len(obj.args), numargs))

    def test_plain_text(self):
        self.assertEqual(list(_normparse(u'hello world')), [u'hello world'])

    def test_escaped_character_only(self):
        self.assertEqual(list(_normparse(u'$$')), [u'$'])

    def test_escaped_character_in_text(self):
        self.assertEqual(list(_normparse(u'a $$ b')), [u'a $ b'])

    def test_escaped_character_at_start(self):
        self.assertEqual(list(_normparse(u'$$ hello')), [u'$ hello'])

    def test_escaped_character_at_end(self):
        self.assertEqual(list(_normparse(u'hello $$')), [u'hello $'])

    def test_escaped_function_delim(self):
        self.assertEqual(list(_normparse(u'a %% b')), [u'a % b'])

    def test_escaped_sep(self):
        self.assertEqual(list(_normparse(u'a ,, b')), [u'a , b'])

    def test_escaped_open_brace(self):
        self.assertEqual(list(_normparse(u'a {{ b')), [u'a { b'])

    def test_escaped_close_brace(self):
        self.assertEqual(list(_normparse(u'a }} b')), [u'a } b'])

    def test_bare_value_delim_kept_intact(self):
        self.assertEqual(list(_normparse(u'a $ b')), [u'a $ b'])

    def test_bare_function_delim_kept_intact(self):
        self.assertEqual(list(_normparse(u'a % b')), [u'a % b'])

    def test_bare_opener_kept_intact(self):
        self.assertEqual(list(_normparse(u'a { b')), [u'a { b'])

    def test_bare_closer_kept_intact(self):
        self.assertEqual(list(_normparse(u'a } b')), [u'a } b'])

    def test_bare_sep_kept_intact(self):
        self.assertEqual(list(_normparse(u'a , b')), [u'a , b'])

    def test_symbol_alone(self):
        parts = list(_normparse(u'$foo'))
        self.assertEqual(len(parts), 1)
        self._assert_symbol(parts[0], u"foo")

    def test_symbol_in_text(self):
        parts = list(_normparse(u'hello $foo world'))
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], u'hello ')
        self._assert_symbol(parts[1], u"foo")
        self.assertEqual(parts[2], u' world')

    def test_symbol_with_braces(self):
        parts = list(_normparse(u'hello${foo}world'))
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], u'hello')
        self._assert_symbol(parts[1], u"foo")
        self.assertEqual(parts[2], u'world')

    def test_unclosed_braces_symbol(self):
        self.assertEqual(list(_normparse(u'a ${ b')), [u'a ${ b'])
    
    def test_empty_braces_symbol(self):
        self.assertEqual(list(_normparse(u'a ${} b')), [u'a ${} b'])

    def test_call_without_args_at_end(self):
        self.assertEqual(list(_normparse(u'foo %bar')), [u'foo %bar'])
    
    def test_call_without_args(self):
        self.assertEqual(list(_normparse(u'foo %bar baz')), [u'foo %bar baz'])

    def test_call_with_unclosed_args(self):
        self.assertEqual(list(_normparse(u'foo %bar{ baz')), [u'foo %bar{ baz'])
    
    def test_call_with_unclosed_multiple_args(self):
        self.assertEqual(list(_normparse(u'foo %bar{bar,bar baz')),
                         [u'foo %bar{bar,bar baz'])

    def test_call_no_args(self):
        parts = list(_normparse(u'%foo{}'))
        self.assertEqual(len(parts), 1)
        self._assert_call(parts[0], u"foo", 0)
    
    def test_call_single_arg(self):
        parts = list(_normparse(u'%foo{bar}'))
        self.assertEqual(len(parts), 1)
        self._assert_call(parts[0], u"foo", 1)
        self.assertEqual(list(_normexpr(parts[0].args[0])), [u'bar'])
    
    def test_call_two_args(self):
        parts = list(_normparse(u'%foo{bar,baz}'))
        self.assertEqual(len(parts), 1)
        self._assert_call(parts[0], u"foo", 2)
        self.assertEqual(list(_normexpr(parts[0].args[0])), [u'bar'])
        self.assertEqual(list(_normexpr(parts[0].args[1])), [u'baz'])
    
    def test_call_with_escaped_sep(self):
        parts = list(_normparse(u'%foo{bar,,baz}'))
        self.assertEqual(len(parts), 1)
        self._assert_call(parts[0], u"foo", 1)
        self.assertEqual(list(_normexpr(parts[0].args[0])), [u'bar,baz'])
    
    def test_call_with_escaped_close(self):
        parts = list(_normparse(u'%foo{bar}}baz}'))
        self.assertEqual(len(parts), 1)
        self._assert_call(parts[0], u"foo", 1)
        self.assertEqual(list(_normexpr(parts[0].args[0])), [u'bar}baz'])
    
def suite():
    return unittest.TestLoader().loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')