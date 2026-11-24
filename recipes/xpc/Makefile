ifeq ($(SDK),macosx26.5)
.PHONY: stage-xpc-type
stage: stage-xpc-type
stage-xpc-type:
	mkdir -p "$(STAGE)/xpc/dst/usr/include/xpc"
	install -m 644 recipes/xpc/xpc.h "$(STAGE)/xpc/dst/usr/include/xpc/"
	$(call header-record,xpc,usr/include/xpc/xpc.h,derived:recipes/xpc/xpc.h,recipes/xpc/Makefile,install the XPC object type required by Security,recipes/xpc/xpc.h recipes/xpc/README.md)
endif
