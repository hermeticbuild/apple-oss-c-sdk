.DEFAULT_GOAL := test

include ../../frameworks/common.mk

.PHONY: test test-dns-sd test-resolver
test: test-dns-sd test-resolver

test-dns-sd:
	$(call test-sdk-link,../../recipes/mDNSResponder/test.c)

test-resolver:
	$(call test-sdk-link,../../recipes/libresolv/test.c,-lresolv $(application-extension-link))
