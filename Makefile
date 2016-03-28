.PHONY: all deb

NAME := speedtest-scripts
VERSION := 1.1.0
ARCH := all
MAINTAINER := Nick Groenen <nick@groenen.me>
DESCRIPTION := Scripts for testing internet bandwidth using speedtest.net
URL := https://github.com/zoni/speedtest-scripts

all: deb

deb:
	test -e _workarea && rm -rf _workarea || true
	mkdir -p _workarea/usr/bin/
	cp -a *.py _workarea/usr/bin/
	fpm -f -t deb -s dir -C _workarea --name "$(NAME)" --version "$(VERSION)" --architecture "$(ARCH)" --maintainer "$(MAINTAINER)" --description "$(DESCRIPTION)" --url "$(URL)" --deb-compression xz --deb-no-default-config-files .
	rm -rf _workarea/
