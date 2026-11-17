# macOS SDK 26.5 C headers for review

377 SDK paths lack an approved disposition, plus
0 installed headers absent from this SDK.
Probe reach is recorded but does not approve an extra header:
it can itself change __has_include behavior.
An installed path
still needs a source and scope review; a missing path needs a
supported include or omit decision. New SDK paths always need review.

## Root-level (107)

- `AppleEXR.h` — proposed review
- `AppleTextureEncoder.h` — proposed review
- `NSSystemDirectories.h` — proposed review
- `SystemHealthClient.h` — proposed review
- `SystemHealthManager.h` — proposed review
- `Xplugin.h` — proposed review
- `__libunwind_config.h` — proposed review
- `aliasdb.h` — proposed review
- `asl.h` — proposed review
- `bitstring.h` — proposed include
- `bootparams.h` — proposed review
- `bootstrap.h` — proposed review
- `bzlib.h` — proposed review
- `cache.h` — proposed review
- `cache_callbacks.h` — proposed review
- `checkint.h` — proposed review
- `com_err.h` — proposed review
- `compression.h` — proposed review
- `curses.h` — proposed review
- `disktab.h` — proposed include
- `dns.h` — proposed review
- `dns_sd.h` — proposed review
- `dns_util.h` — proposed review
- `dtrace.h` — proposed review
- `eti.h` — proposed review
- `expat.h` — proposed review
- `expat_config.h` — proposed review
- `expat_external.h` — proposed review
- `form.h` — proposed review
- `fsproperties.h` — proposed include
- `fstab.h` — proposed include
- `get_compat.h` — proposed review
- `gssapi.h` — proposed review
- `histedit.h` — proposed review
- `iso646.h` — proposed include
- `krb5.h` — proposed review
- `lber.h` — proposed review
- `lber_types.h` — proposed review
- `ldap.h` — proposed review
- `ldap_cdefs.h` — proposed review
- `ldap_features.h` — proposed review
- `ldap_schema.h` — proposed review
- `ldap_utf8.h` — proposed review
- `ldif.h` — proposed review
- `libc.h` — proposed include
- `libcharset.h` — proposed review
- `libmanagedconfigurationfiles.h` — proposed review
- `libunwind.h` — proposed review
- `localcharset.h` — proposed review
- `membership.h` — proposed include
- `menu.h` — proposed review
- `monitor.h` — proposed include
- `mpool.h` — proposed include
- `nameser.h` — proposed review
- `nc_tparm.h` — proposed review
- `ncurses.h` — proposed review
- `ncurses_dll.h` — proposed review
- `nlist.h` — proposed include
- `notify.h` — proposed include
- `notify_keys.h` — proposed include
- `ntsid.h` — proposed include
- `panel.h` — proposed review
- `pcap-bpf.h` — proposed review
- `pcap-namedb.h` — proposed review
- `pcap.h` — proposed review
- `printerdb.h` — proposed review
- `printf.h` — proposed include
- `profile.h` — proposed review
- `pthread.h` — proposed include
- `pthread_impl.h` — proposed review
- `pthread_spis.h` — proposed review
- `ranlib.h` — proposed include
- `readpassphrase.h` — proposed include
- `removefile.h` — proposed include
- `resolv.h` — proposed review
- `rune.h` — proposed include
- `sched.h` — proposed include
- `sgtty.h` — proposed include
- `slapi-plugin.h` — proposed review
- `sqlite3.h` — proposed review
- `sqlite3ext.h` — proposed review
- `stab.h` — proposed include
- `standards.h` — proposed include
- `stddef.h` — proposed include
- `strhash.h` — proposed include
- `string_x86.h` — proposed include
- `stringlist.h` — proposed include
- `struct.h` — proposed include
- `sysdir.h` — proposed review
- `term.h` — proposed review
- `term_entry.h` — proposed review
- `termcap.h` — proposed review
- `tic.h` — proposed review
- `timeconv.h` — proposed include
- `timingsafe.h` — proposed include
- `ttyent.h` — proposed include
- `tzfile.h` — proposed review
- `unctrl.h` — proposed review
- `unwind.h` — proposed review — Clang resource overlap
- `unwind_arm_ehabi.h` — proposed review
- `unwind_itanium.h` — proposed review
- `usbuf.h` — proposed review
- `util.h` — proposed include
- `utmp.h` — proposed include
- `vproc.h` — proposed review
- `xattr_flags.h` — proposed include
- `xcselect.h` — proposed review

## `Spatial/` (34)

- `Spatial/Base.h` — proposed review
- `Spatial/SPAffineTransform3D.h` — proposed review
- `Spatial/SPAffineTransform3DFloat.h` — proposed review
- `Spatial/SPAngle.h` — proposed review
- `Spatial/SPAngleFloat.h` — proposed review
- `Spatial/SPPoint3D.h` — proposed review
- `Spatial/SPPoint3DFloat.h` — proposed review
- `Spatial/SPPose3D.h` — proposed review
- `Spatial/SPPose3DFloat.h` — proposed review
- `Spatial/SPProjectiveTransform3D.h` — proposed review
- `Spatial/SPProjectiveTransform3DFloat.h` — proposed review
- `Spatial/SPRay3D.h` — proposed review
- `Spatial/SPRay3DFloat.h` — proposed review
- `Spatial/SPRect3D.h` — proposed review
- `Spatial/SPRect3DFloat.h` — proposed review
- `Spatial/SPRotation3D.h` — proposed review
- `Spatial/SPRotation3DFloat.h` — proposed review
- `Spatial/SPRotationAxis3D.h` — proposed review
- `Spatial/SPRotationAxis3DFloat.h` — proposed review
- `Spatial/SPScaledPose3D.h` — proposed review
- `Spatial/SPScaledPose3DFloat.h` — proposed review
- `Spatial/SPSize3D.h` — proposed review
- `Spatial/SPSize3DFloat.h` — proposed review
- `Spatial/SPSphericalCoordinates3D.h` — proposed review
- `Spatial/SPSphericalCoordinates3DFloat.h` — proposed review
- `Spatial/SPVector3D.h` — proposed review
- `Spatial/SPVector3DFloat.h` — proposed review
- `Spatial/Spatial.h` — proposed review
- `Spatial/SpatialEnumerations.h` — proposed review
- `Spatial/SpatialTypeConversion.h` — proposed review
- `Spatial/Structures.h` — proposed review
- `Spatial/StructuresFloat.h` — proposed review
- `Spatial/StructuresPackedDouble.h` — proposed review
- `Spatial/StucturesPackedFloat.h` — proposed review

## `AppleArchive/` (19)

- `AppleArchive/AAArchiveStream.h` — proposed review
- `AppleArchive/AAByteStream.h` — proposed review
- `AppleArchive/AACustomArchiveStream.h` — proposed review
- `AppleArchive/AACustomByteStream.h` — proposed review
- `AppleArchive/AADefs.h` — proposed review
- `AppleArchive/AAEntryACLBlob.h` — proposed review
- `AppleArchive/AAEntryAttributes.h` — proposed review
- `AppleArchive/AAEntryMessage.h` — proposed review
- `AppleArchive/AAEntryXATBlob.h` — proposed review
- `AppleArchive/AAFieldKeys.h` — proposed review
- `AppleArchive/AAFlagSet.h` — proposed review
- `AppleArchive/AAHeader.h` — proposed review
- `AppleArchive/AAPathList.h` — proposed review
- `AppleArchive/AEAAuthData.h` — proposed review
- `AppleArchive/AEAContext.h` — proposed review
- `AppleArchive/AEADefs.h` — proposed review
- `AppleArchive/AEAStreams.h` — proposed review
- `AppleArchive/AppleArchive.h` — proposed review
- `AppleArchive/AppleEncryptedArchive.h` — proposed review

## `architecture/` (18)

- `architecture/alignment.h` — proposed review
- `architecture/arm/asm_help.h` — proposed review
- `architecture/arm/byte_order.h` — proposed review
- `architecture/arm/cframe.h` — proposed review
- `architecture/arm/reg_help.h` — proposed review
- `architecture/i386/alignment.h` — proposed review
- `architecture/i386/asm_help.h` — proposed review
- `architecture/i386/byte_order.h` — proposed review
- `architecture/i386/cpu.h` — proposed review
- `architecture/i386/desc.h` — proposed review
- `architecture/i386/fpu.h` — proposed review
- `architecture/i386/frame.h` — proposed review
- `architecture/i386/io.h` — proposed review
- `architecture/i386/pio.h` — proposed review
- `architecture/i386/reg_help.h` — proposed review
- `architecture/i386/sel.h` — proposed review
- `architecture/i386/table.h` — proposed review
- `architecture/i386/tss.h` — proposed review

## `netinet/` (17)

- `netinet/bootp.h` — proposed review
- `netinet/icmp6.h` — proposed include
- `netinet/icmp_var.h` — proposed review
- `netinet/if_ether.h` — proposed review
- `netinet/igmp.h` — proposed review
- `netinet/igmp_var.h` — proposed review
- `netinet/in_pcb.h` — proposed include
- `netinet/in_var.h` — proposed review
- `netinet/ip6.h` — proposed include
- `netinet/ip_icmp.h` — proposed include
- `netinet/ip_var.h` — proposed review
- `netinet/tcp_fsm.h` — proposed review
- `netinet/tcp_seq.h` — proposed review
- `netinet/tcp_timer.h` — proposed include
- `netinet/tcp_var.h` — proposed include
- `netinet/tcpip.h` — proposed review
- `netinet/udp_var.h` — proposed review

## `rpcsvc/` (17)

- `rpcsvc/bootparam_prot.h` — proposed review
- `rpcsvc/klm_prot.h` — proposed review
- `rpcsvc/mount.h` — proposed review
- `rpcsvc/nfs_prot.h` — proposed review
- `rpcsvc/nlm_prot.h` — proposed review
- `rpcsvc/rex.h` — proposed review
- `rpcsvc/rnusers.h` — proposed review
- `rpcsvc/rquota.h` — proposed review
- `rpcsvc/rstat.h` — proposed review
- `rpcsvc/rusers.h` — proposed review
- `rpcsvc/rwall.h` — proposed review
- `rpcsvc/sm_inter.h` — proposed review
- `rpcsvc/spray.h` — proposed review
- `rpcsvc/yp.h` — proposed review
- `rpcsvc/yp_prot.h` — proposed review
- `rpcsvc/ypclnt.h` — proposed review
- `rpcsvc/yppasswd.h` — proposed review

## `mach/` (13)

- `mach/arm/asm.h` — proposed review
- `mach/arm64/asm.h` — proposed review
- `mach/clock_reply.h` — proposed include
- `mach/exc.h` — proposed include
- `mach/i386/asm.h` — proposed review
- `mach/mach_eventlink.h` — proposed include
- `mach/mach_right.h` — proposed include
- `mach/mach_vm.h` — proposed include
- `mach/mach_voucher.h` — proposed include
- `mach/memory_entry.h` — proposed include
- `mach/port_obj.h` — proposed include
- `mach/sync.h` — proposed include
- `mach/vm_task.h` — proposed include

## `rpc/` (12)

- `rpc/auth.h` — proposed include
- `rpc/auth_unix.h` — proposed include
- `rpc/clnt.h` — proposed include
- `rpc/pmap_clnt.h` — proposed include
- `rpc/pmap_prot.h` — proposed include
- `rpc/pmap_rmt.h` — proposed include
- `rpc/rpc.h` — proposed include
- `rpc/rpc_msg.h` — proposed include
- `rpc/svc.h` — proposed include
- `rpc/svc_auth.h` — proposed include
- `rpc/types.h` — proposed include
- `rpc/xdr.h` — proposed include

## `bsm/` (11)

- `bsm/audit_domain.h` — proposed include
- `bsm/audit_errno.h` — proposed include
- `bsm/audit_fcntl.h` — proposed include
- `bsm/audit_filter.h` — proposed review
- `bsm/audit_internal.h` — proposed include
- `bsm/audit_kevents.h` — proposed include
- `bsm/audit_record.h` — proposed include
- `bsm/audit_session.h` — proposed review
- `bsm/audit_socket_type.h` — proposed include
- `bsm/audit_uevents.h` — proposed review
- `bsm/libbsm.h` — proposed review

## `odmodule/` (9)

- `odmodule/odconnection.h` — proposed review
- `odmodule/odconstants.h` — proposed review
- `odmodule/odcore.h` — proposed review
- `odmodule/odcredential.h` — proposed review
- `odmodule/odcstr.h` — proposed review
- `odmodule/odmodule.h` — proposed review
- `odmodule/odmoduleconfig.h` — proposed review
- `odmodule/odrequest.h` — proposed review
- `odmodule/odtypes.h` — proposed review

## `netinet6/` (8)

- `netinet6/ah.h` — proposed review
- `netinet6/esp.h` — proposed review
- `netinet6/in6_var.h` — proposed review
- `netinet6/ipcomp.h` — proposed review
- `netinet6/ipsec.h` — proposed include
- `netinet6/nd6.h` — proposed review
- `netinet6/raw_ip6.h` — proposed review
- `netinet6/scope6_var.h` — proposed include

## `os/` (8)

- `os/activity.h` — proposed review
- `os/arch/arm64.h` — proposed review
- `os/log.h` — proposed review
- `os/proc.h` — proposed review
- `os/security_config.h` — proposed include
- `os/signpost.h` — proposed review
- `os/trace.h` — proposed review
- `os/trace_base.h` — proposed review

## `pexpert/` (8)

- `pexpert/boot.h` — proposed review
- `pexpert/i386/boot.h` — proposed review
- `pexpert/i386/efi.h` — proposed review
- `pexpert/i386/protos.h` — proposed review
- `pexpert/machine/boot.h` — proposed review
- `pexpert/machine/protos.h` — proposed review
- `pexpert/pexpert.h` — proposed review
- `pexpert/protos.h` — proposed review

## `sasl/` (8)

- `sasl/gai.h` — proposed review
- `sasl/hmac-md5.h` — proposed review
- `sasl/md5.h` — proposed review
- `sasl/md5global.h` — proposed review
- `sasl/prop.h` — proposed review
- `sasl/sasl.h` — proposed review
- `sasl/saslplug.h` — proposed review
- `sasl/saslutil.h` — proposed review

## `security/` (8)

- `security/audit/audit_ioctl.h` — proposed review
- `security/openpam.h` — proposed review
- `security/openpam_attr.h` — proposed review
- `security/openpam_version.h` — proposed review
- `security/pam_appl.h` — proposed review
- `security/pam_constants.h` — proposed review
- `security/pam_modules.h` — proposed review
- `security/pam_types.h` — proposed review

## `servers/` (7)

- `servers/bootstrap.h` — proposed review
- `servers/bootstrap_defs.h` — proposed review
- `servers/key_defs.h` — proposed review
- `servers/ls_defs.h` — proposed review
- `servers/netname.h` — proposed review
- `servers/netname_defs.h` — proposed review
- `servers/nm_defs.h` — proposed review

## `ffi/` (6)

- `ffi/ffi.h` — proposed review
- `ffi/ffitarget.h` — proposed review
- `ffi/ffitarget_arm64.h` — proposed review
- `ffi/ffitarget_armv7.h` — proposed review
- `ffi/ffitarget_x86.h` — proposed review
- `ffi/tramp.h` — proposed review

## `EndpointSecurity/` (5)

- `EndpointSecurity/ESClient.h` — proposed review
- `EndpointSecurity/ESMessage.h` — proposed review
- `EndpointSecurity/ESMessageCore.h` — proposed review
- `EndpointSecurity/ESTypes.h` — proposed review
- `EndpointSecurity/EndpointSecurity.h` — proposed review

## `arpa/` (5)

- `arpa/ftp.h` — proposed include
- `arpa/nameser.h` — proposed review
- `arpa/nameser_compat.h` — proposed include
- `arpa/telnet.h` — proposed include
- `arpa/tftp.h` — proposed include

## `kern/` (4)

- `kern/exc_guard.h` — proposed review
- `kern/exc_resource.h` — proposed review
- `kern/kcdata.h` — proposed review
- `kern/kern_cdata.h` — proposed review

## `nfs/` (4)

- `nfs/nfs.h` — proposed review
- `nfs/nfsproto.h` — proposed review
- `nfs/rpcv2.h` — proposed review
- `nfs/xdr_subs.h` — proposed review

## `protocols/` (4)

- `protocols/routed.h` — proposed include
- `protocols/rwhod.h` — proposed include
- `protocols/talkd.h` — proposed include
- `protocols/timed.h` — proposed include

## `pthread/` (4)

- `pthread/introspection.h` — proposed include
- `pthread/pthread_spis.h` — proposed include
- `pthread/spawn.h` — proposed include
- `pthread/stack_np.h` — proposed include

## `tidy/` (4)

- `tidy/buffio.h` — proposed review
- `tidy/platform.h` — proposed review
- `tidy/tidy.h` — proposed review
- `tidy/tidyenum.h` — proposed review

## `gssapi/` (3)

- `gssapi/gssapi.h` — proposed review
- `gssapi/gssapi_generic.h` — proposed review
- `gssapi/gssapi_krb5.h` — proposed review

## `hvf/` (3)

- `hvf/RenderContext.h` — proposed review
- `hvf/Scaler.h` — proposed review
- `hvf/Types.h` — proposed review

## `krb5/` (3)

- `krb5/krb5.h` — proposed review
- `krb5/locate_plugin.h` — proposed review
- `krb5/preauth_plugin.h` — proposed review

## `miscfs/` (3)

- `miscfs/devfs/devfs.h` — proposed review
- `miscfs/specfs/specdev.h` — proposed review
- `miscfs/union/union.h` — proposed review

## `arm64/` (2)

- `arm64/hv/hv_kern_types.h` — proposed review
- `arm64/mte.h` — proposed review

## `libDER/` (2)

- `libDER/DERItem.h` — proposed review
- `libDER/libDER_config.h` — proposed review

## `readline/` (2)

- `readline/history.h` — proposed review
- `readline/readline.h` — proposed review

## `sys/` (2)

- `sys/rbtree.h` — proposed include
- `sys/syscall.h` — proposed review

## `arm/` (1)

- `arm/cpu_capabilities_public.h` — proposed review

## `atm/` (1)

- `atm/atm_types.h` — proposed review

## `bank/` (1)

- `bank/bank_types.h` — proposed review

## `corpses/` (1)

- `corpses/task_corpse.h` — proposed review

## `default_pager/` (1)

- `default_pager/default_pager_types.h` — proposed review

## `device/` (1)

- `device/device_port.h` — proposed review

## `dispatch/` (1)

- `dispatch/introspection.h` — proposed include

## `hfs/` (1)

- `hfs/hfs_mount.h` — proposed review

## `i386/` (1)

- `i386/user_ldt.h` — proposed review

## `infiniband/` (1)

- `infiniband/verbs.h` — proposed review

## `libkern/` (1)

- `libkern/machine/OSByteOrder.h` — proposed review

## `mach_debug/` (1)

- `mach_debug/mach_debug.h` — proposed include

## `netkey/` (1)

- `netkey/keysock.h` — proposed review

## `networkext/` (1)

- `networkext/ne_socket.h` — proposed review

## `vfs/` (1)

- `vfs/vfs_support.h` — proposed review

## `voucher/` (1)

- `voucher/ipc_pthread_priority_types.h` — proposed review

## `xar/` (1)

- `xar/xar.h` — proposed review

## Installation-only headers needing review
