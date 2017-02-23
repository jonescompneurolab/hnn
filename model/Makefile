# Makefile for nrn
# v 0.2.14
# rev 2012-07-26 (SL: added vecevent.mod)
# last rev: (SL: created)

# macros
ECHO = /bin/echo
MV = /bin/mv
UNAME := $(shell uname)

PROJ = nrntest

MOD = ar.mod ca.mod cad.mod cat.mod kca.mod km.mod vecevent.mod

vpath %.mod mod/

# make rules
x86_64/special : mod
	nrnivmodl $<
	# $(MV) bin/$@ bin/$@.autobak
	# $(CC) $(CFLAGS) -o bin/$@ $+
	@$(ECHO) '-------------------------------------------------------'
	@$(ECHO) 'make built [$@] successfully. Now go save the stupid princess.'
	@$(ECHO) '-------------------------------------------------------'

# clean
.PHONY: clean
clean :
	rm -f x86_64/*
