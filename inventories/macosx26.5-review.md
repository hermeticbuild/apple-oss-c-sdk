# macOS SDK 26.5 C headers for review

482 SDK paths lack an approved disposition, plus
337 installed headers absent from this SDK
that are not reached by the generated C probe.
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

## `sys/` (72)

- `sys/_structs.h` — proposed include
- `sys/_types/_offsetof.h` — proposed include
- `sys/_types/_ptrdiff_t.h` — proposed include
- `sys/_types/_ucontext64.h` — proposed include
- `sys/acct.h` — proposed include
- `sys/buf.h` — proposed include
- `sys/commpage.h` — proposed include
- `sys/conf.h` — proposed include
- `sys/dir.h` — proposed include
- `sys/disk.h` — proposed include
- `sys/dkstat.h` — proposed include
- `sys/domain.h` — proposed include
- `sys/dtrace.h` — proposed include
- `sys/dtrace_glue.h` — proposed include
- `sys/dtrace_impl.h` — proposed include
- `sys/endian.h` — proposed include
- `sys/ev.h` — proposed include
- `sys/fasttrap.h` — proposed include
- `sys/fasttrap_isa.h` — proposed include
- `sys/filedesc.h` — proposed include
- `sys/fileport.h` — proposed include
- `sys/fsgetpath.h` — proposed include
- `sys/gmon.h` — proposed include
- `sys/ioctl_compat.h` — proposed include
- `sys/kdebug.h` — proposed include
- `sys/kdebug_signpost.h` — proposed include
- `sys/kern_event.h` — proposed include
- `sys/kernel.h` — proposed include
- `sys/kernel_types.h` — proposed include
- `sys/lctx.h` — proposed include
- `sys/loadable_fs.h` — proposed include
- `sys/lockf.h` — proposed include
- `sys/lockstat.h` — proposed include
- `sys/log_data.h` — proposed include
- `sys/malloc.h` — proposed include
- `sys/mbuf.h` — proposed include
- `sys/msgbuf.h` — proposed include
- `sys/netport.h` — proposed include
- `sys/pipe.h` — proposed include
- `sys/posix_sem.h` — proposed include
- `sys/posix_shm.h` — proposed include
- `sys/protosw.h` — proposed include
- `sys/ptrace.h` — proposed include
- `sys/quota.h` — proposed include
- `sys/rbtree.h` — proposed include
- `sys/reboot.h` — proposed include
- `sys/resourcevar.h` — proposed include
- `sys/sbuf.h` — proposed include
- `sys/sdt.h` — proposed include
- `sys/signalvar.h` — proposed include
- `sys/snapshot.h` — proposed include
- `sys/socketvar.h` — proposed include
- `sys/sys_domain.h` — proposed include
- `sys/syscall.h` — proposed review
- `sys/timeb.h` — proposed include
- `sys/trace.h` — proposed include
- `sys/tty.h` — proposed include
- `sys/ttychars.h` — proposed include
- `sys/ttydev.h` — proposed include
- `sys/ubc.h` — proposed include
- `sys/unpcb.h` — proposed include
- `sys/user.h` — proposed include
- `sys/utfconv.h` — proposed include
- `sys/vadvise.h` — proposed include
- `sys/vcmd.h` — proposed include
- `sys/vmmeter.h` — proposed include
- `sys/vmparam.h` — proposed include
- `sys/vnode.h` — proposed include
- `sys/vnode_if.h` — proposed include
- `sys/vsock.h` — proposed include
- `sys/vstat.h` — proposed include
- `sys/xattr.h` — proposed include

## `mach/` (35)

- `mach/arm/asm.h` — proposed review
- `mach/arm/ndr_def.h` — proposed include
- `mach/arm/sdt_isa.h` — proposed include
- `mach/arm/syscall_sw.h` — proposed include
- `mach/arm/traps.h` — proposed include
- `mach/arm64/asm.h` — proposed review
- `mach/audit_triggers_types.h` — proposed include
- `mach/bootstrap.h` — proposed include
- `mach/clock_reply.h` — proposed include
- `mach/doubleagent_types.h` — proposed include
- `mach/dyld_pager.h` — proposed include
- `mach/exc.h` — proposed include
- `mach/host_reboot.h` — proposed include
- `mach/i386/asm.h` — proposed review
- `mach/i386/ndr_def.h` — proposed include
- `mach/i386/sdt_isa.h` — proposed include
- `mach/mach_eventlink.h` — proposed include
- `mach/mach_param.h` — proposed include
- `mach/mach_right.h` — proposed include
- `mach/mach_syscalls.h` — proposed include
- `mach/mach_vm.h` — proposed include
- `mach/mach_voucher.h` — proposed include
- `mach/machine/asm.h` — proposed include
- `mach/machine/ndr_def.h` — proposed include
- `mach/machine/sdt.h` — proposed include
- `mach/machine/sdt_isa.h` — proposed include
- `mach/memory_entry.h` — proposed include
- `mach/mig_strncpy_zerofill_support.h` — proposed include
- `mach/mig_voucher_support.h` — proposed include
- `mach/port_obj.h` — proposed include
- `mach/sdt.h` — proposed include
- `mach/shared_memory_server.h` — proposed include
- `mach/shared_region.h` — proposed include
- `mach/sync.h` — proposed include
- `mach/vm_task.h` — proposed include

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
- `architecture/i386/asm_help.h` — proposed include
- `architecture/i386/byte_order.h` — proposed review
- `architecture/i386/cpu.h` — proposed include
- `architecture/i386/desc.h` — proposed include
- `architecture/i386/fpu.h` — proposed review
- `architecture/i386/frame.h` — proposed review
- `architecture/i386/io.h` — proposed include
- `architecture/i386/pio.h` — proposed include
- `architecture/i386/reg_help.h` — proposed include
- `architecture/i386/sel.h` — proposed include
- `architecture/i386/table.h` — proposed include
- `architecture/i386/tss.h` — proposed include

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

## `os/` (10)

- `os/activity.h` — proposed review
- `os/arch/arm64.h` — proposed review
- `os/atomic.h` — proposed include
- `os/log.h` — proposed include
- `os/overflow.h` — proposed include
- `os/proc.h` — proposed review
- `os/security_config.h` — proposed include
- `os/signpost.h` — proposed review
- `os/trace.h` — proposed include
- `os/trace_base.h` — proposed review

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

## `machine/` (5)

- `machine/_limits.h` — proposed include
- `machine/byte_order.h` — proposed include
- `machine/fasttrap_isa.h` — proposed include
- `machine/profile.h` — proposed include
- `machine/vmparam.h` — proposed include

## `arm/` (4)

- `arm/cpu_capabilities_public.h` — proposed review
- `arm/fasttrap_isa.h` — proposed include
- `arm/profile.h` — proposed include
- `arm/vmparam.h` — proposed include

## `i386/` (4)

- `i386/fasttrap_isa.h` — proposed include
- `i386/profile.h` — proposed include
- `i386/user_ldt.h` — proposed review
- `i386/vmparam.h` — proposed include

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

- `libDER/DERItem.h` — proposed include
- `libDER/libDER_config.h` — proposed include

## `readline/` (2)

- `readline/history.h` — proposed review
- `readline/readline.h` — proposed review

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

### `sys/` (133)

- `sys/_types/_user32_itimerval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user32_itimerval.h
- `sys/_types/_user32_ntptimeval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user32_ntptimeval.h
- `sys/_types/_user32_timespec.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user32_timespec.h
- `sys/_types/_user32_timeval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user32_timeval.h
- `sys/_types/_user32_timex.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user32_timex.h
- `sys/_types/_user64_itimerval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user64_itimerval.h
- `sys/_types/_user64_ntptimeval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user64_ntptimeval.h
- `sys/_types/_user64_timespec.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user64_timespec.h
- `sys/_types/_user64_timeval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user64_timeval.h
- `sys/_types/_user64_timex.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user64_timex.h
- `sys/_types/_user_timespec.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user_timespec.h
- `sys/_types/_user_timeval.h` — SOURCE_TREES: sources/xnu/bsd/sys/_types/_user_timeval.h
- `sys/aio_kern.h` — SOURCE_TREES: sources/xnu/bsd/sys/aio_kern.h
- `sys/attr_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/attr_private.h
- `sys/bitstring.h` — SOURCE_TREES: sources/xnu/bsd/sys/bitstring.h
- `sys/bsdtask_info.h` — SOURCE_TREES: sources/xnu/bsd/sys/bsdtask_info.h
- `sys/buf_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/buf_internal.h
- `sys/coalition.h` — SOURCE_TREES: sources/xnu/bsd/sys/coalition.h
- `sys/coalition_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/coalition_private.h
- `sys/code_signing.h` — SOURCE_TREES: sources/xnu/bsd/sys/code_signing.h
- `sys/code_signing_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/code_signing_internal.h
- `sys/codedir_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/codedir_internal.h
- `sys/codesign.h` — SOURCE_TREES: sources/xnu/bsd/sys/codesign.h
- `sys/commpage_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/commpage_private.h
- `sys/content_protection.h` — SOURCE_TREES: sources/xnu/bsd/sys/content_protection.h
- `sys/cprotect.h` — SOURCE_TREES: sources/xnu/bsd/sys/cprotect.h
- `sys/crossarch.h` — SOURCE_TREES: sources/xnu/bsd/sys/crossarch.h
- `sys/csr.h` — SOURCE_TREES: sources/xnu/bsd/sys/csr.h
- `sys/decmpfs.h` — SOURCE_TREES: sources/xnu/bsd/sys/decmpfs.h
- `sys/dirent_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/dirent_private.h
- `sys/dis_tables.h` — SOURCE_TREES: sources/xnu/bsd/sys/dis_tables.h
- `sys/disk_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/disk_private.h
- `sys/disklabel.h` — SOURCE_TREES: sources/xnu/bsd/sys/disklabel.h
- `sys/disktab.h` — SOURCE_TREES: sources/xnu/bsd/sys/disktab.h
- `sys/dmap.h` — SOURCE_TREES: sources/xnu/bsd/sys/dmap.h
- `sys/doc_tombstone.h` — SOURCE_TREES: sources/xnu/bsd/sys/doc_tombstone.h
- `sys/dtrace_ptss.h` — SOURCE_TREES: sources/xnu/bsd/sys/dtrace_ptss.h
- `sys/event_log.h` — SOURCE_TREES: sources/xnu/bsd/sys/event_log.h
- `sys/event_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/event_private.h
- `sys/eventhandler.h` — SOURCE_TREES: sources/xnu/bsd/sys/eventhandler.h
- `sys/eventvar.h` — SOURCE_TREES: sources/xnu/bsd/sys/eventvar.h
- `sys/exec.h` — SOURCE_TREES: sources/xnu/bsd/sys/exec.h
- `sys/fasttrap_impl.h` — SOURCE_TREES: sources/xnu/bsd/sys/fasttrap_impl.h
- `sys/fbt.h` — SOURCE_TREES: sources/xnu/bsd/sys/fbt.h
- `sys/fcntl_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/fcntl_private.h
- `sys/file_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/file_internal.h
- `sys/fsctl.h` — SOURCE_TREES: sources/xnu/bsd/sys/fsctl.h
- `sys/fsevents.h` — SOURCE_TREES: sources/xnu/bsd/sys/fsevents.h
- `sys/fsgetpath_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/fsgetpath_private.h
- `sys/fslog.h` — SOURCE_TREES: sources/xnu/bsd/sys/fslog.h
- `sys/guarded.h` — SOURCE_TREES: sources/xnu/bsd/sys/guarded.h
- `sys/imageboot.h` — SOURCE_TREES: sources/xnu/bsd/sys/imageboot.h
- `sys/imgact.h` — SOURCE_TREES: sources/xnu/bsd/sys/imgact.h
- `sys/imgsrc.h` — SOURCE_TREES: sources/xnu/bsd/sys/imgsrc.h
- `sys/ipcs.h` — SOURCE_TREES: sources/xnu/bsd/sys/ipcs.h
- `sys/kas_info.h` — SOURCE_TREES: sources/xnu/bsd/sys/kas_info.h
- `sys/kdebug_common.h` — SOURCE_TREES: sources/xnu/bsd/sys/kdebug_common.h
- `sys/kdebug_kernel.h` — SOURCE_TREES: sources/xnu/bsd/sys/kdebug_kernel.h
- `sys/kdebug_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/kdebug_private.h
- `sys/kdebug_triage.h` — SOURCE_TREES: sources/xnu/bsd/sys/kdebug_triage.h
- `sys/kern_control_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_control_private.h
- `sys/kern_debug.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_debug.h
- `sys/kern_event_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_event_private.h
- `sys/kern_memorystatus.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_memorystatus.h
- `sys/kern_memorystatus_freeze.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_memorystatus_freeze.h
- `sys/kern_memorystatus_notify.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_memorystatus_notify.h
- `sys/kern_memorystatus_xnu.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_memorystatus_xnu.h
- `sys/kern_overrides.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_overrides.h
- `sys/kern_sysctl.h` — SOURCE_TREES: sources/xnu/bsd/sys/kern_sysctl.h
- `sys/kpi_mbuf.h` — SOURCE_TREES: sources/xnu/bsd/sys/kpi_mbuf.h
- `sys/kpi_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/kpi_private.h
- `sys/kpi_socket.h` — SOURCE_TREES: sources/xnu/bsd/sys/kpi_socket.h
- `sys/kpi_socketfilter.h` — SOURCE_TREES: sources/xnu/bsd/sys/kpi_socketfilter.h
- `sys/ktrace.h` — SOURCE_TREES: sources/xnu/bsd/sys/ktrace.h
- `sys/linker_set.h` — SOURCE_TREES: sources/xnu/bsd/sys/linker_set.h
- `sys/lockdown_mode.h` — SOURCE_TREES: sources/xnu/bsd/sys/lockdown_mode.h
- `sys/mach_swapon.h` — SOURCE_TREES: sources/xnu/bsd/sys/mach_swapon.h
- `sys/mcache.h` — SOURCE_TREES: sources/xnu/bsd/sys/mcache.h
- `sys/md5.h` — SOURCE_TREES: sources/xnu/bsd/sys/md5.h
- `sys/mem_acct_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/mem_acct_private.h
- `sys/memory_maintenance.h` — SOURCE_TREES: sources/xnu/bsd/sys/memory_maintenance.h
- `sys/mman_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/mman_private.h
- `sys/monotonic.h` — SOURCE_TREES: sources/xnu/bsd/sys/monotonic.h
- `sys/mount_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/mount_internal.h
- `sys/munge.h` — SOURCE_TREES: sources/xnu/bsd/sys/munge.h
- `sys/namei.h` — SOURCE_TREES: sources/xnu/bsd/sys/namei.h
- `sys/netboot.h` — SOURCE_TREES: sources/xnu/bsd/sys/netboot.h
- `sys/os_log_coprocessor.h` — SOURCE_TREES: sources/xnu/bsd/sys/os_log_coprocessor.h
- `sys/persona.h` — SOURCE_TREES: sources/xnu/bsd/sys/persona.h
- `sys/pgo.h` — SOURCE_TREES: sources/xnu/bsd/sys/pgo.h
- `sys/preoslog.h` — SOURCE_TREES: sources/xnu/bsd/sys/preoslog.h
- `sys/priv.h` — SOURCE_TREES: sources/xnu/bsd/sys/priv.h
- `sys/proc_info_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_info_private.h
- `sys/proc_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_internal.h
- `sys/proc_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_private.h
- `sys/proc_require.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_require.h
- `sys/proc_ro.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_ro.h
- `sys/proc_uuid_policy.h` — SOURCE_TREES: sources/xnu/bsd/sys/proc_uuid_policy.h
- `sys/process_policy.h` — SOURCE_TREES: sources/xnu/bsd/sys/process_policy.h
- `sys/pthread_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/pthread_internal.h
- `sys/pthread_shims.h` — SOURCE_TREES: sources/xnu/bsd/sys/pthread_shims.h
- `sys/reason.h` — SOURCE_TREES: sources/xnu/bsd/sys/reason.h
- `sys/resource_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/resource_private.h
- `sys/sdt_impl.h` — SOURCE_TREES: sources/xnu/bsd/sys/sdt_impl.h
- `sys/sem_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/sem_internal.h
- `sys/sfi.h` — SOURCE_TREES: sources/xnu/bsd/sys/sfi.h
- `sys/shm_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/shm_internal.h
- `sys/socket_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/socket_private.h
- `sys/sockio_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/sockio_private.h
- `sys/spawn_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/spawn_internal.h
- `sys/stackshot.h` — SOURCE_TREES: sources/xnu/bsd/sys/stackshot.h
- `sys/subr_prf.h` — SOURCE_TREES: sources/xnu/bsd/sys/subr_prf.h
- `sys/sys_domain_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/sys_domain_private.h
- `sys/sysent.h` — SOURCE_TREES: sources/xnu/bsd/sys/sysent.h
- `sys/systm.h` — SOURCE_TREES: sources/xnu/bsd/sys/systm.h
- `sys/systrace_args.h` — SOURCE_TREES: sources/xnu/bsd/sys/systrace_args.h
- `sys/tprintf.h` — SOURCE_TREES: sources/xnu/bsd/sys/tprintf.h
- `sys/tree.h` — SOURCE_TREES: sources/xnu/bsd/sys/tree.h
- `sys/trust_caches.h` — SOURCE_TREES: sources/xnu/bsd/sys/trust_caches.h
- `sys/trusted_execution_monitor.h` — SOURCE_TREES: sources/xnu/bsd/sys/trusted_execution_monitor.h
- `sys/ubc_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/ubc_internal.h
- `sys/uio_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/uio_internal.h
- `sys/ulock.h` — SOURCE_TREES: sources/xnu/bsd/sys/ulock.h
- `sys/unicode.h` — SOURCE_TREES: sources/xnu/bsd/sys/unicode.h
- `sys/ux_exception.h` — SOURCE_TREES: sources/xnu/bsd/sys/ux_exception.h
- `sys/variant_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/variant_internal.h
- `sys/vfs_context.h` — SOURCE_TREES: sources/xnu/bsd/sys/vfs_context.h
- `sys/vlimit.h` — SOURCE_TREES: sources/xnu/bsd/sys/vlimit.h
- `sys/vnode_internal.h` — SOURCE_TREES: sources/xnu/bsd/sys/vnode_internal.h
- `sys/vsock_domain.h` — SOURCE_TREES: sources/xnu/bsd/sys/vsock_domain.h
- `sys/vsock_private.h` — SOURCE_TREES: sources/xnu/bsd/sys/vsock_private.h
- `sys/vsock_transport.h` — SOURCE_TREES: sources/xnu/bsd/sys/vsock_transport.h
- `sys/work_interval.h` — SOURCE_TREES: sources/xnu/bsd/sys/work_interval.h

### `corecrypto/` (42)

- `corecrypto/cc.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc.h
- `corecrypto/cc_config.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_config.h
- `corecrypto/cc_error.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_error.h
- `corecrypto/cc_fault_canary.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_fault_canary.h
- `corecrypto/cc_impl.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_impl.h
- `corecrypto/cc_lock.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_lock.h
- `corecrypto/cc_macros.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_macros.h
- `corecrypto/cc_priv.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_priv.h
- `corecrypto/cc_runtime_config.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cc_runtime_config.h
- `corecrypto/ccaes.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccaes.h
- `corecrypto/ccasn1.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccasn1.h
- `corecrypto/ccchacha20poly1305.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccchacha20poly1305.h
- `corecrypto/cccmac.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cccmac.h
- `corecrypto/ccder.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccder.h
- `corecrypto/ccder_blob.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccder_blob.h
- `corecrypto/ccdes.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdes.h
- `corecrypto/ccdigest.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdigest.h
- `corecrypto/ccdigest_priv.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdigest_priv.h
- `corecrypto/ccdrbg.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdrbg.h
- `corecrypto/ccdrbg_df.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdrbg_df.h
- `corecrypto/ccdrbg_impl.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccdrbg_impl.h
- `corecrypto/ccentropy.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccentropy.h
- `corecrypto/cchkdf.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cchkdf.h
- `corecrypto/cchmac.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cchmac.h
- `corecrypto/cckprng.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cckprng.h
- `corecrypto/ccmd4.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmd4.h
- `corecrypto/ccmode.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmode.h
- `corecrypto/ccmode_factory.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmode_factory.h
- `corecrypto/ccmode_impl.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmode_impl.h
- `corecrypto/ccmode_siv.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmode_siv.h
- `corecrypto/ccmode_siv_hmac.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccmode_siv_hmac.h
- `corecrypto/ccn.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccn.h
- `corecrypto/ccpad.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccpad.h
- `corecrypto/ccrng.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccrng.h
- `corecrypto/ccrng_crypto.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccrng_crypto.h
- `corecrypto/ccrng_fortuna.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccrng_fortuna.h
- `corecrypto/ccrng_schedule.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccrng_schedule.h
- `corecrypto/ccrsa.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccrsa.h
- `corecrypto/ccsha1.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccsha1.h
- `corecrypto/ccsha2.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/ccsha2.h
- `corecrypto/cczp.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/cczp.h
- `corecrypto/fipspost_trace.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/corecrypto/fipspost_trace.h

### `mach/` (41)

- `mach/arcade_upcall_server.h` — MIG: generated:system-mig:arcade_upcall_server.h via generate_mig.py
- `mach/audit_triggers_server.h` — MIG: generated:system-mig:audit_triggers_server.h via generate_mig.py
- `mach/clock_reply_server.h` — MIG: generated:system-mig:clock_reply_server.h via generate_mig.py
- `mach/coalition.h` — SOURCE_TREES: sources/xnu/osfmk/mach/coalition.h
- `mach/coalition_notification_server.h` — MIG: generated:system-mig:coalition_notification_server.h via generate_mig.py
- `mach/doubleagent_mig_server.h` — MIG: generated:system-mig:doubleagent_mig_server.h via generate_mig.py
- `mach/dyld_kernel_fixups.h` — SOURCE_TREES: sources/xnu/osfmk/mach/dyld_kernel_fixups.h
- `mach/events_info.h` — SOURCE_TREES: sources/xnu/osfmk/mach/events_info.h
- `mach/exc_server.h` — MIG: generated:system-mig:exc_server.h via generate_mig.py
- `mach/exclaves.h` — SOURCE_TREES: sources/xnu/osfmk/mach/exclaves.h
- `mach/exclaves_l4.h` — SOURCE_TREES: sources/xnu/osfmk/mach/exclaves_l4.h
- `mach/fairplayd_notification_server.h` — MIG: generated:system-mig:fairplayd_notification_server.h via generate_mig.py
- `mach/i386/syscall_sw.h` — SOURCE_TREES: sources/xnu/osfmk/mach/i386/syscall_sw.h
- `mach/iocompressionstats_notification_server.h` — MIG: generated:system-mig:iocompressionstats_notification_server.h via generate_mig.py
- `mach/mach_eventlink_types.h` — SOURCE_TREES: sources/xnu/osfmk/mach/mach_eventlink_types.h
- `mach/mach_exc_server.h` — MIG: generated:system-mig:mach_exc_server.h via generate_mig.py
- `mach/mach_time_private.h` — SOURCE_TREES: sources/xnu/osfmk/mach/mach_time_private.h
- `mach/machine/syscall_sw.h` — SOURCE_TREES: sources/xnu/osfmk/mach/machine/syscall_sw.h
- `mach/memory_error_notification_server.h` — MIG: generated:system-mig:memory_error_notification_server.h via generate_mig.py
- `mach/memory_object.h` — SOURCE_TREES: sources/xnu/osfmk/mach/memory_object.h
- `mach/memory_object_control.h` — SOURCE_TREES: sources/xnu/osfmk/mach/memory_object_control.h
- `mach/mig_log.h` — SOURCE_TREES: sources/xnu/osfmk/mach/mig_log.h
- `mach/mk_timer.h` — SOURCE_TREES: sources/xnu/osfmk/mach/mk_timer.h
- `mach/mk_traps.h` — SOURCE_TREES: sources/xnu/osfmk/mach/mk_traps.h
- `mach/msg_type.h` — SOURCE_TREES: sources/xnu/osfmk/mach/msg_type.h
- `mach/notify_server.h` — MIG: generated:system-mig:notify_server.h via generate_mig.py
- `mach/prof_types.h` — SOURCE_TREES: sources/xnu/osfmk/mach/prof_types.h
- `mach/resource_monitors.h` — SOURCE_TREES: sources/xnu/osfmk/mach/resource_monitors.h
- `mach/sfi_class.h` — SOURCE_TREES: sources/xnu/osfmk/mach/sfi_class.h
- `mach/syscall_sw.h` — SOURCE_TREES: sources/xnu/osfmk/mach/syscall_sw.h
- `mach/sysdiagnose_notification_server.h` — MIG: generated:system-mig:sysdiagnose_notification_server.h via generate_mig.py
- `mach/task_access_server.h` — MIG: generated:system-mig:task_access_server.h via generate_mig.py
- `mach/task_ledger.h` — SOURCE_TREES: sources/xnu/osfmk/mach/task_ledger.h
- `mach/task_policy_private.h` — SOURCE_TREES: sources/xnu/osfmk/mach/task_policy_private.h
- `mach/telemetry_notification_server.h` — MIG: generated:system-mig:telemetry_notification_server.h via generate_mig.py
- `mach/thread_policy_private.h` — SOURCE_TREES: sources/xnu/osfmk/mach/thread_policy_private.h
- `mach/vfs_nspace_server.h` — MIG: generated:system-mig:vfs_nspace_server.h via generate_mig.py
- `mach/vm_reclaim.h` — SOURCE_TREES: sources/xnu/osfmk/mach/vm_reclaim.h
- `mach/vm_reclaim_private.h` — SOURCE_TREES: sources/xnu/osfmk/mach/vm_reclaim_private.h
- `mach/vm_region_private.h` — SOURCE_TREES: sources/xnu/osfmk/mach/vm_region_private.h
- `mach/vm_types_unsafe.h` — SOURCE_TREES: sources/xnu/osfmk/mach/vm_types_unsafe.h

### `os/` (32)

- `os/alloc_util.h` — SOURCE_TREES: sources/xnu/libkern/os/alloc_util.h
- `os/atomic_private.h` — SOURCE_TREES: sources/xnu/libkern/os/atomic_private.h
- `os/atomic_private_arch.h` — SOURCE_TREES: sources/xnu/libkern/os/atomic_private_arch.h
- `os/atomic_private_impl.h` — SOURCE_TREES: sources/xnu/libkern/os/atomic_private_impl.h
- `os/base_private.h` — SOURCE_TREES: sources/xnu/libkern/os/base_private.h
- `os/cpp_util.h` — SOURCE_TREES: sources/xnu/libkern/os/cpp_util.h
- `os/cxx_safe_buffers.h` — SOURCE_TREES: sources/xnu/libkern/os/cxx_safe_buffers.h
- `os/eventlink_private.h` — SOURCE_TREES: sources/libdispatch/os/eventlink_private.h
- `os/firehose.h` — SOURCE_TREES: sources/xnu/libkern/os/firehose.h
- `os/firehose_buffer_private.h` — SOURCE_TREES: sources/libdispatch/os/firehose_buffer_private.h
- `os/firehose_server_private.h` — SOURCE_TREES: sources/libdispatch/os/firehose_server_private.h
- `os/generic_unix_base.h` — SOURCE_TREES: sources/libdispatch/os/generic_unix_base.h
- `os/generic_win_base.h` — SOURCE_TREES: sources/libdispatch/os/generic_win_base.h
- `os/hash.h` — SOURCE_TREES: sources/xnu/libkern/os/hash.h
- `os/log_encode.h` — SOURCE_TREES: sources/xnu/libkern/os/log_encode.h
- `os/log_encode_types.h` — SOURCE_TREES: sources/xnu/libkern/os/log_encode_types.h
- `os/log_internal.h` — SOURCE_TREES: sources/xnu/libkern/os/log_internal.h
- `os/log_mem.h` — SOURCE_TREES: sources/xnu/libkern/os/log_mem.h
- `os/log_private.h` — SOURCE_TREES: sources/xnu/libkern/os/log_private.h
- `os/log_queue.h` — SOURCE_TREES: sources/xnu/libkern/os/log_queue.h
- `os/object_private.h` — SOURCE_TREES: sources/libdispatch/os/object_private.h
- `os/ptrtools.h` — SOURCE_TREES: sources/xnu/libkern/os/ptrtools.h
- `os/reason_private.h` — SOURCE_TREES: sources/xnu/libkern/os/reason_private.h
- `os/refcnt.h` — SOURCE_TREES: sources/xnu/libkern/os/refcnt.h
- `os/refcnt_internal.h` — SOURCE_TREES: sources/xnu/libkern/os/refcnt_internal.h
- `os/system_event_log.h` — SOURCE_TREES: sources/xnu/libkern/os/system_event_log.h
- `os/trace_internal.h` — SOURCE_TREES: sources/xnu/libkern/os/trace_internal.h
- `os/voucher_activity_private.h` — SOURCE_TREES: sources/libdispatch/os/voucher_activity_private.h
- `os/voucher_private.h` — SOURCE_TREES: sources/libdispatch/os/voucher_private.h
- `os/workgroup_interval_private.h` — SOURCE_TREES: sources/libdispatch/os/workgroup_interval_private.h
- `os/workgroup_object_private.h` — SOURCE_TREES: sources/libdispatch/os/workgroup_object_private.h
- `os/workgroup_private.h` — SOURCE_TREES: sources/libdispatch/os/workgroup_private.h

### `image4/` (21)

- `image4/coprocessor.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor.h
- `image4/coprocessor/ap.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/ap.h
- `image4/coprocessor/ap_local.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/ap_local.h
- `image4/coprocessor/bootpc.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/bootpc.h
- `image4/coprocessor/cryptex1.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/cryptex1.h
- `image4/coprocessor/sep.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/sep.h
- `image4/coprocessor/vma2.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/vma2.h
- `image4/coprocessor/vma3.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/vma3.h
- `image4/coprocessor/x86.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/coprocessor/x86.h
- `image4/cryptex1/nonce.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/cryptex1/nonce.h
- `image4/cs/pmap.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/cs/pmap.h
- `image4/cs/traps.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/cs/traps.h
- `image4/environment.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/environment.h
- `image4/identifier.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/identifier.h
- `image4/image4.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/image4.h
- `image4/restricted/environment.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/restricted/environment.h
- `image4/shim/base.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/shim/base.h
- `image4/shim/types.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/shim/types.h
- `image4/trust.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/trust.h
- `image4/trust_evaluation.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/trust_evaluation.h
- `image4/types.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/image4/types.h

### `img4/` (17)

- `img4/4xnu.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/4xnu.h
- `img4/api.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/api.h
- `img4/chip.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip.h
- `img4/chip_ap.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_ap.h
- `img4/chip_ap_category.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_ap_category.h
- `img4/chip_ap_software.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_ap_software.h
- `img4/chip_cryptex1.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_cryptex1.h
- `img4/chip_sep.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_sep.h
- `img4/chip_x86.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/chip_x86.h
- `img4/firmware.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/firmware.h
- `img4/image.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/image.h
- `img4/img4.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/img4.h
- `img4/nonce.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/nonce.h
- `img4/object.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/object.h
- `img4/runtime.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/runtime.h
- `img4/shim.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/shim.h
- `img4/shim_xnu.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/img4/shim_xnu.h

### `CoreEntitlements/` (11)

- `CoreEntitlements/CoreEntitlements.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/CoreEntitlements.h
- `CoreEntitlements/CoreEntitlementsPriv.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/CoreEntitlementsPriv.h
- `CoreEntitlements/Entitlements.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Entitlements.h
- `CoreEntitlements/EntitlementsPriv.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/EntitlementsPriv.h
- `CoreEntitlements/Errors.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Errors.h
- `CoreEntitlements/Index.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Index.h
- `CoreEntitlements/QueryHelpers.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/QueryHelpers.h
- `CoreEntitlements/Result.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Result.h
- `CoreEntitlements/Runtime.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Runtime.h
- `CoreEntitlements/Serialization.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/Serialization.h
- `CoreEntitlements/der_vm.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreEntitlements/der_vm.h

### `libDER/` (9)

- `libDER/DER_CertCrl.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_CertCrl.h
- `libDER/DER_CodecUtils.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_CodecUtils.h
- `libDER/DER_Decode.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_Decode.h
- `libDER/DER_Digest.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_Digest.h
- `libDER/DER_Encode.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_Encode.h
- `libDER/DER_Keys.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/DER_Keys.h
- `libDER/asn1Types.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/asn1Types.h
- `libDER/libDER.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/libDER.h
- `libDER/oids.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/libDER/oids.h

### `machine/` (8)

- `machine/cons.h` — SOURCE_TREES: sources/xnu/bsd/machine/cons.h
- `machine/dis_tables.h` — SOURCE_TREES: sources/xnu/bsd/machine/dis_tables.h
- `machine/disklabel.h` — SOURCE_TREES: sources/xnu/bsd/machine/disklabel.h
- `machine/exec.h` — SOURCE_TREES: sources/xnu/bsd/machine/exec.h
- `machine/psl.h` — SOURCE_TREES: sources/xnu/bsd/machine/psl.h
- `machine/ptrace.h` — SOURCE_TREES: sources/xnu/bsd/machine/ptrace.h
- `machine/reg.h` — SOURCE_TREES: sources/xnu/bsd/machine/reg.h
- `machine/smp.h` — SOURCE_TREES: sources/xnu/bsd/machine/smp.h

### `i386/` (5)

- `i386/dis_tables.h` — SOURCE_TREES: sources/xnu/bsd/i386/dis_tables.h
- `i386/disklabel.h` — SOURCE_TREES: sources/xnu/bsd/i386/disklabel.h
- `i386/psl.h` — SOURCE_TREES: sources/xnu/bsd/i386/psl.h
- `i386/ptrace.h` — SOURCE_TREES: sources/xnu/bsd/i386/ptrace.h
- `i386/reg.h` — SOURCE_TREES: sources/xnu/bsd/i386/reg.h

### Root-level (4)

- `Endian.h` — SOURCE_GROUPS: sources/CarbonHeaders/Endian.h
- `asm.h` — SOURCE_TREES: sources/Libc/include/asm.h
- `authentication.h` — SOURCE_TREES: sources/Libc/include/authentication.h
- `kvm.h` — SOURCE_TREES: sources/Libc/include/kvm.h

### `arm/` (4)

- `arm/disklabel.h` — SOURCE_TREES: sources/xnu/bsd/arm/disklabel.h
- `arm/psl.h` — SOURCE_TREES: sources/xnu/bsd/arm/psl.h
- `arm/ptrace.h` — SOURCE_TREES: sources/xnu/bsd/arm/ptrace.h
- `arm/reg.h` — SOURCE_TREES: sources/xnu/bsd/arm/reg.h

### `CoreTrust/` (2)

- `CoreTrust/CTConfig.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreTrust/CTConfig.h
- `CoreTrust/CTEvaluate.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/CoreTrust/CTEvaluate.h

### `acpi/` (2)

- `acpi/Acpi.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/acpi/Acpi.h
- `acpi/Acpi_v1.h` — SOURCE_TREES: sources/xnu/EXTERNAL_HEADERS/acpi/Acpi_v1.h

### `exclavekit/` (2)

- `exclavekit/os/lock.h` — SOURCE_TREES: sources/libplatform/include/exclavekit/os/lock.h
- `exclavekit/os/lock_private.h` — SOURCE_TREES: sources/libplatform/include/exclavekit/os/lock_private.h

### `FreeBSD/` (1)

- `FreeBSD/nl_types.h` — SOURCE_TREES: sources/Libc/include/FreeBSD/nl_types.h

### `NetBSD/` (1)

- `NetBSD/utmpx.h` — header-sources.tsv: generated:libc via inputs/header-sources.tsv:NetBSD/utmpx.h

### `architecture/` (1)

- `architecture/arm/fenv.h` — Libm derivation: sources/Libm/Source/ARM/fenv.h

### `rpc/` (1)

- `rpc/pmap_wakeup.h` — SOURCE_GROUPS: sources/Libinfo/rpc.subproj/pmap_wakeup.h
