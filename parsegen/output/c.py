# This file is part of Parsegen and is licensed as follows:
#
# Copyright (c) 2012 Will Speak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from parsegen.output import *
	
class COutputContext(CallbackOutputContext):
	"""C Output Context
	
	Represents the context required to write out to a C file.
	"""
	
	def __init__(self, *args):
		CallbackOutputContext.__init__(self, *args)
		self.register_callback(
			self._write_header_to_file, CallbackOutputContext.PRE)
		self.register_callback(
			self._write_helpers_to_file, CallbackOutputContext.PRE)
		self.register_callback(
			self._write_symbol_to_file, CallbackOutputContext.MAIN)
		self.register_callback(
			self._write_user_code_to_file, CallbackOutputContext.POST)
	
	def _write_section_header(self, heading, file):
		"""Write Section Header
	
		Prints a commented header to mark a section within the output file.
		"""
	
		file.write('/' + '*' * 77 + '\n')
		file.write(" * {0} *\n".format(heading.center(73)))
		file.write(' ' + '*' * 77 + '/\n\n')

	def _write_header_to_file(self, file):
		"""Write Header to File
	
		Writes the beginning of the file. This is everything that should appear 
		before the utilities.
		"""
	
		self._write_section_header("global includes", file)
	
		file.write('#include <stdio.h>\n#include <stdlib.h>\n#include "{0}"\n\n'
			.format(self.options.lexer_include))

	def _write_helpers_to_file(self, file):
		"""Write Helpers to File
	
		Write out any functions and definitions required for the automaton to
		work. These would usually be the `eat` and `peek` definitions.
		"""
	
		self._write_section_header("utility methods", file)
	
		# Global variables to keep track of tokens from the lexer
		file.write("static " + self.options.token_type + "next_token;\n")
		file.write("static int token_buffered = 0;\n\n")
		
		# Write out the body of the _peek_next_token funciton
		file.write(
			self.options.token_type + " " + self.options.prefix +
			"_peek_next_token(void)\n{\n")
		file.write("\tif (!token_buffered) {\n")
		file.write("\t\tnext_token = " + self.options.lexer_function + ";\n")
		file.write("\t\ttoken_buffered = 1;\n")
		file.write("\t}\n")
		file.write("\treturn next_token;\n")
		file.write("}\n\n")
		
		file.write(
			"int " + self.options.prefix + "_eat_token(" +
			self.options.token_type + " expected_token)\n{\n")
		file.write(
			"\t" + self.options.token_type + " tok = " + self.options.prefix +
			"_peek_next_token();\n")
			
		file.write("\tif (token == expected_token) {\n")
		file.write("\t\ttoken_buffered = 0;\n")
		file.write("\t\treturn 1;\n")
		file.write("\t}\n")
		file.write("\treturn 0;\n")
		file.write("}\n\n")

	def _write_symbol_to_file(self, name, symbol, file):
		"""Write Symbol to File
		
		Writes out a symbol to the file. This function is responsible for
		iterating over all the expansions in the symbol and writing them out.
		"""
		self._write_symbol_function_begin(name, symbol, file)
		for expansion in symbol.expansions:
			self._write_body_for_expansion(name, expansion, file)
		self._write_symbol_function_end(file)
		

	def _get_counts(self, symbol):
		"""Get Counts
		
		Returns the number of nodes in a given symbol that are nonterminals.
		"""
		node_count = 0

		for expansion in symbol.expansions:
			n = 0
			for e in expansion:
				if not e in self.grammar.header.terminals:
					n += 1
			if n > node_count: node_count = n
		return node_count

	def _write_symbol_function_begin(self, name, symbol, ofile):
		"""Write Symbol Function Begin
		
		Prints the beginning of a function that parses a given symbol.
		"""
		
		node_count = self._get_counts(symbol)
		
		ofile.write("static {0} {1}(void)\n{{\n".format(
			self.options.node_type, name))
		ofile.write("\t{0} nodes[{1}];\n".format(
			self.options.node_type, node_count))
		ofile.write(
			"\t{0} token {1}_peek_next_token();\n\tswitch(token) {{\n".format(
				self.options.token_type, self.options.prefix))
		if symbol.is_nullable():
			ofile.write("\tdefault:\n")
			ofile.write("\t\treturn 0;\n\n")

	def _write_body_for_expansion(self, name, expansion, file):
		"""Write Body for Expansion
		
		Writes out the case statement that will be responsible for parsing a 
		given expansion of a symbol.
		"""
	
		if not expansion:
			# Lambda transition, handled later
			return
	
		terms = self.predictions_for_expansion(expansion)
	
		for term in terms:
			file.write(
				'\tcase {0}:\n'.format(self.grammar.header.terminals[term]))

		params = []
		node = 0
	
		for sym in expansion:
			if sym in self.grammar.header.terminals:
				file.write(
					"\t\tif (!eat_terminal({0}))\n\t\t\tgoto error;\n".format(
						self.grammar.header.terminals[sym]))
				params.append(self.grammar.header.terminals[sym])
			else:
				node_temp = "nodes[{0}]".format(node)
				node += 1
				file.write("\t\t{0} = {1}();\n".format(
					node_temp,
					sym
				))
				params.append(node_temp)
	
		file.write("\t\ttoken_action_{0}({1});\n".format(name, ", ".join(params)))
		file.write('\t\tbreak;\n\n')
	
	def _write_symbol_function_end(self, file):
		"""Write Symbol Function End
		
		Closes off the function that parses a symbol.
		"""
		file.write("\t}\n}\n\n")

	def _write_user_code_to_file(self, file):
		"""Write User Code to File
	
		Writes a given block of code to the file prefixed with a user code
		header.
		"""
	
		self._write_section_header('user code', file)
		file.write(self.grammar.user_code)

register_context("c", COutputContext)