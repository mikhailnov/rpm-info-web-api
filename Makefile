all:
	cc -fPIC -shared -o amon_rpm-info-web-api.so amon.c -ldl

install:
	mkdir -p $(DESTDIR)/usr/local/lib/
	cp amon_rpm-info-web-api.so $(DESTDIR)/usr/local/lib/
	if [ ! -e $(DESTDIR)/etc/rpm-info-web-api.conf ]; then \
		mkdir -p $(DESTDIR)/etc/ ; \
		install -m0664 rpm-info-web-api.conf $(DESTDIR)/etc/ ; \
	fi
	@echo
	@echo "1) Change /tmp/rpms in /etc/rpm-info-web-api.conf"
	@echo "2) Copy *.cgi manually"
	@echo "3) Install bashlib https://github.com/mikhailnov/bashlib into PATH"
