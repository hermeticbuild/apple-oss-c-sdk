FOUNDATION_TBD_SHA256 := 8d0449b42907aa840dd0f6ac9f2072015ca55e2cc38759f261dde4ee9cc38e9f
FOUNDATION_STAGE = $(STAGE)/Foundation.framework

Foundation: require-stage CoreFoundation-versioned-tbd
	@test -n "$(FOUNDATION_TBD)" || { echo "Set FOUNDATION_TBD to the qualified SDK Gen 0.0.4 stub." >&2; exit 1; }
	printf '%s  %s\n' '$(FOUNDATION_TBD_SHA256)' '$(FOUNDATION_TBD)' | shasum -a 256 -c -
	$(call stage-framework-headers,Foundation,NSObjCRuntime NSRange NSObject NSString NSArray NSDictionary NSData NSError NSURL NSValue NSNumber NSDate)
	install -m 644 "$(FOUNDATION_TBD)" "$(FOUNDATION_STAGE)/Foundation.tbd"
	patch -s -f -F 0 -V none -p1 -d "$(FOUNDATION_STAGE)" < Foundation/reexport-corefoundation.patch

test-Foundation:
	$(call test-sdk-link,Foundation/test.m,-fobjc-arc -framework Foundation -lobjc)

test-Foundation-modules:
	$(call test-objc-modules,Foundation)
