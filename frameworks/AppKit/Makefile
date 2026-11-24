APPKIT_STAGE = $(STAGE)/AppKit.framework

AppKit: require-stage Foundation
AppKit: $(filter ApplicationServices,$(FRAMEWORKS))
	@test -f "$(OBJC4_INSTALL)/usr/include/objc/NSObject.h" || { echo "Set OBJC4_INSTALL to the pinned objc4 installation." >&2; exit 1; }
	$(call stage-framework-headers,AppKit,NSColor NSResponder NSApplication NSView NSWindow)
	$(call installapi,$(objc-installapi) \
		-install_name /System/Library/Frameworks/AppKit.framework/AppKit \
		-reexport_library "$(FOUNDATION_STAGE)/Foundation.tbd" \
		$(if $(filter ApplicationServices,$(FRAMEWORKS)),-reexport_library "$(APPLICATION_SERVICES_STAGE)/ApplicationServices.tbd") \
		-extra-public-header "$(APPKIT_STAGE)/Headers/AppKit.h",$(APPKIT_STAGE)/AppKit.tbd,objective-c)
