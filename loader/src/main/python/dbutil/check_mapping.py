#!/usr/bin/env python
import sqlite3

class CheckMapping:
	def __init__(self, dbfile):
		self.conn = sqlite3.connect(dbfile)
		self.c = self.conn.cursor()
		print "init CheckMapping"
		print "using dbfile:", dbfile

	def has_mapping(self, symbol):
		t = (symbol,)
		self.c.execute('select * from identifiers where symbol=?', t)

		return self.c.fetchone()

#if __name__ == "__main__":
#	check = CheckMapping("/Users/testuser/Development/db/srcdb/mappings.db")
#	if not check.has_mapping("ARV11"):
#		print "not found ARV11"
#	else:
#		print "found ARV11"
#
#	if not check.has_mapping("FUS9"): 
#		print "not found FUS9"
#	else:
#		print "found FUS9"
