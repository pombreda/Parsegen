from parsegen import *
from nose.tools import *

def new_symbol(string):
	return Symbol(string)

class TestSymbols():
	
	def test_create(self):
		assert new_symbol("FOO").is_term()
		assert new_symbol("FOO_BAR").is_term()
		assert not new_symbol("foo").is_term()
		assert not new_symbol("baz").is_term()
		assert not new_symbol("hello_world").is_term()
		assert new_symbol(" ok\t")
	
	@raises(IdentifierError)
	def test_invalid_1(self):
		new_symbol(" not Ok ")
	
	@raises(IdentifierError)
	def test_invalid_2(self):
		new_symbol("not-ok!either")

	def test_first(self):
		assert new_symbol("FOO").first() == set(["FOO"])
		assert new_symbol("A").first() == set(["A"])
		assert new_symbol(" AVERO").first() == set(["AVERO"])
		assert new_symbol(" bax").first() == set([])
	
	def test_no_expansions_new(self):
		assert len(new_symbol("a").expansions) == 0
		
	def test_expansions(self):
		a = new_symbol('bip')
		a.push_expansion([])
		assert len(a.expansions) == 1

	@raises(TerminalExpansionError)
	def test_expanding_terminal(self):
		new_symbol("TERMINAL_SYMBOL").push_expansion([])
		
	def test_nullable(self):
		assert new_symbol("nonterm").nullable()
		assert not new_symbol("BAWER").nullable()
		
		a = new_symbol("a")
		
		a.push_expansion([new_symbol("RAWR")])
		assert not a.nullable()
		
		a.push_expansion([])
		assert a.nullable()
		
		a.push_expansion([new_symbol("hello"), new_symbol("world")])
		assert a.nullable()
		
		b = new_symbol("b")
		assert b.nullable()
		
		b.push_expansion([new_symbol("bar")])
		b.push_expansion([new_symbol("bax")])
		assert not b.nullable()
		
		
	def test_first_with_expansions(self):
		a = new_symbol("a")
		
		a.push_expansion([new_symbol("B")])
		assert a.first() == set(["B"])
		
		a.push_expansion([])
		assert a.first() == set(["B"])
		
		a.push_expansion([new_symbol("CAR")])
		assert a.first() == set(["B", "CAR"])
		
		a.push_expansion([new_symbol("b"), new_symbol("FUXX")])
		assert a.first() == set(["B", "CAR", "FUXX"])
		
		b = new_symbol('bar')
		b.push_expansion([new_symbol("lamb"), new_symbol("FUD"), new_symbol("FOD")])
		print b.first()
		assert b.first() == set(["FUD"])
	