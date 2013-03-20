#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""Wrapper for QueryParser."""


from google.appengine._internal import antlr3
from google.appengine._internal.antlr3 import tree
from google.appengine.api.search import QueryLexer
from google.appengine.api.search import QueryParser


class QueryException(Exception):
  """An error occurred while parsing the query input string."""


class QueryLexerWithErrors(QueryLexer.QueryLexer):
  """An overridden Lexer that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      QueryException: always.
    """
    raise QueryException(msg)


class QueryParserWithErrors(QueryParser.QueryParser):
  """An overridden Parser that raises exceptions."""

  def emitErrorMessage(self, msg):
    """Raise an exception if the input fails to parse correctly.

    Overriding the default, which normally just prints a message to
    stderr.

    Arguments:
      msg: the error message
    Raises:
      QueryException: always.
    """
    raise QueryException(msg)


def CreateParser(query):
  """Creates a Query Parser."""
  input_string = antlr3.ANTLRStringStream(query)
  lexer = QueryLexerWithErrors(input_string)
  tokens = antlr3.CommonTokenStream(lexer)
  parser = QueryParserWithErrors(tokens)
  return parser


def Parse(query):
  """Parses a query and returns an ANTLR tree."""
  parser = CreateParser(query)
  try:
    return parser.query()
  except Exception, e:
    raise QueryException(e.message)


def Simplify(parser_return):
  """Simplifies the output of the parser."""
  if parser_return.tree:
    return _SimplifyNode(parser_return.tree)
  return parser_return


def _SimplifyNode(node):
  """Simplifies the node removing singleton conjunctions and others."""
  if not node.getType():
    return _SimplifyNode(node.children[0])
  elif node.getType() == QueryParser.CONJUNCTION and node.getChildCount() == 1:
    return _SimplifyNode(node.children[0])
  elif node.getType() == QueryParser.DISJUNCTION and node.getChildCount() == 1:
    return _SimplifyNode(node.children[0])
  elif (node.getType() == QueryParser.RESTRICTION and node.getChildCount() == 2
        and node.children[0].getType() == QueryParser.GLOBAL):
    return _SimplifyNode(node.children[1])
  elif (node.getType() == QueryParser.VALUE and node.getChildCount() == 2 and
        (node.children[0].getType() == QueryParser.WORD or
         node.children[0].getType() == QueryParser.STRING or
         node.children[0].getType() == QueryParser.NUMBER)):
    return _SimplifyNode(node.children[1])
  elif ((node.getType() == QueryParser.EQ or node.getType() == QueryParser.HAS)
        and node.getChildCount() == 1):
    return _SimplifyNode(node.children[0])
  for i, child in enumerate(node.children):
    node.setChild(i, _SimplifyNode(child))
  return node


def CreateQueryNode(text, type):
  token = tree.CommonTreeAdaptor().createToken(tokenType=type, text=text)
  return tree.CommonTree(token)


def GetQueryNodeText(node):
  """Returns the text from the node, handling that it could be unicode."""
  return node.getText().encode('utf-8')


def GetPhraseQueryNodeText(node):
  """Returns the text from a query node."""
  text = GetQueryNodeText(node)
  if text:



    if text[0] == '"' and text[-1] == '"':
      text = text[1:-1]
  return text
