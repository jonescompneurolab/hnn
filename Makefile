# Makefile for model - compiles mod files for use by NEURON
# first rev: (SL: created)

# macros
UNAME := $(shell uname)

vpath %.mod mod/

# make rules
x86_64/special : mod
	nrnivmodl $<

# clean
.PHONY: clean
clean :
	rm -f x86_64/*
