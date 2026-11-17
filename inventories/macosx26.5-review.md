# macOS SDK 26.5 C headers for review

277 paths absent from the C installation. These were not reached
by the current C probe and have no reviewed omit rule. Clang resource
overlaps still require an API-parity decision.

## Root-level (73)

- `AppleEXR.h`
- `AppleTextureEncoder.h`
- `NSSystemDirectories.h`
- `SystemHealthClient.h`
- `SystemHealthManager.h`
- `Xplugin.h`
- `__libunwind_config.h`
- `aliasdb.h`
- `asl.h`
- `bootparams.h`
- `bootstrap.h`
- `bzlib.h`
- `cache.h`
- `cache_callbacks.h`
- `checkint.h`
- `com_err.h`
- `compression.h`
- `curses.h`
- `dns.h`
- `dns_sd.h`
- `dns_util.h`
- `dtrace.h`
- `eti.h`
- `expat.h`
- `expat_config.h`
- `expat_external.h`
- `form.h`
- `get_compat.h`
- `gssapi.h`
- `histedit.h`
- `krb5.h`
- `lber.h`
- `lber_types.h`
- `ldap.h`
- `ldap_cdefs.h`
- `ldap_features.h`
- `ldap_schema.h`
- `ldap_utf8.h`
- `ldif.h`
- `libcharset.h`
- `libmanagedconfigurationfiles.h`
- `libunwind.h`
- `localcharset.h`
- `menu.h`
- `nameser.h`
- `nc_tparm.h`
- `ncurses.h`
- `ncurses_dll.h`
- `panel.h`
- `pcap-bpf.h`
- `pcap-namedb.h`
- `pcap.h`
- `printerdb.h`
- `profile.h`
- `pthread_impl.h`
- `pthread_spis.h`
- `resolv.h`
- `slapi-plugin.h`
- `sqlite3.h`
- `sqlite3ext.h`
- `sysdir.h`
- `term.h`
- `term_entry.h`
- `termcap.h`
- `tic.h`
- `tzfile.h`
- `unctrl.h`
- `unwind.h` — Clang resource overlap
- `unwind_arm_ehabi.h`
- `unwind_itanium.h`
- `usbuf.h`
- `vproc.h`
- `xcselect.h`

## `Spatial/` (34)

- `Spatial/Base.h`
- `Spatial/SPAffineTransform3D.h`
- `Spatial/SPAffineTransform3DFloat.h`
- `Spatial/SPAngle.h`
- `Spatial/SPAngleFloat.h`
- `Spatial/SPPoint3D.h`
- `Spatial/SPPoint3DFloat.h`
- `Spatial/SPPose3D.h`
- `Spatial/SPPose3DFloat.h`
- `Spatial/SPProjectiveTransform3D.h`
- `Spatial/SPProjectiveTransform3DFloat.h`
- `Spatial/SPRay3D.h`
- `Spatial/SPRay3DFloat.h`
- `Spatial/SPRect3D.h`
- `Spatial/SPRect3DFloat.h`
- `Spatial/SPRotation3D.h`
- `Spatial/SPRotation3DFloat.h`
- `Spatial/SPRotationAxis3D.h`
- `Spatial/SPRotationAxis3DFloat.h`
- `Spatial/SPScaledPose3D.h`
- `Spatial/SPScaledPose3DFloat.h`
- `Spatial/SPSize3D.h`
- `Spatial/SPSize3DFloat.h`
- `Spatial/SPSphericalCoordinates3D.h`
- `Spatial/SPSphericalCoordinates3DFloat.h`
- `Spatial/SPVector3D.h`
- `Spatial/SPVector3DFloat.h`
- `Spatial/Spatial.h`
- `Spatial/SpatialEnumerations.h`
- `Spatial/SpatialTypeConversion.h`
- `Spatial/Structures.h`
- `Spatial/StructuresFloat.h`
- `Spatial/StructuresPackedDouble.h`
- `Spatial/StucturesPackedFloat.h`

## `AppleArchive/` (19)

- `AppleArchive/AAArchiveStream.h`
- `AppleArchive/AAByteStream.h`
- `AppleArchive/AACustomArchiveStream.h`
- `AppleArchive/AACustomByteStream.h`
- `AppleArchive/AADefs.h`
- `AppleArchive/AAEntryACLBlob.h`
- `AppleArchive/AAEntryAttributes.h`
- `AppleArchive/AAEntryMessage.h`
- `AppleArchive/AAEntryXATBlob.h`
- `AppleArchive/AAFieldKeys.h`
- `AppleArchive/AAFlagSet.h`
- `AppleArchive/AAHeader.h`
- `AppleArchive/AAPathList.h`
- `AppleArchive/AEAAuthData.h`
- `AppleArchive/AEAContext.h`
- `AppleArchive/AEADefs.h`
- `AppleArchive/AEAStreams.h`
- `AppleArchive/AppleArchive.h`
- `AppleArchive/AppleEncryptedArchive.h`

## `rpcsvc/` (17)

- `rpcsvc/bootparam_prot.h`
- `rpcsvc/klm_prot.h`
- `rpcsvc/mount.h`
- `rpcsvc/nfs_prot.h`
- `rpcsvc/nlm_prot.h`
- `rpcsvc/rex.h`
- `rpcsvc/rnusers.h`
- `rpcsvc/rquota.h`
- `rpcsvc/rstat.h`
- `rpcsvc/rusers.h`
- `rpcsvc/rwall.h`
- `rpcsvc/sm_inter.h`
- `rpcsvc/spray.h`
- `rpcsvc/yp.h`
- `rpcsvc/yp_prot.h`
- `rpcsvc/ypclnt.h`
- `rpcsvc/yppasswd.h`

## `netinet/` (11)

- `netinet/bootp.h`
- `netinet/icmp_var.h`
- `netinet/if_ether.h`
- `netinet/igmp.h`
- `netinet/igmp_var.h`
- `netinet/in_var.h`
- `netinet/ip_var.h`
- `netinet/tcp_fsm.h`
- `netinet/tcp_seq.h`
- `netinet/tcpip.h`
- `netinet/udp_var.h`

## `architecture/` (9)

- `architecture/alignment.h`
- `architecture/arm/asm_help.h`
- `architecture/arm/byte_order.h`
- `architecture/arm/cframe.h`
- `architecture/arm/reg_help.h`
- `architecture/i386/alignment.h`
- `architecture/i386/byte_order.h`
- `architecture/i386/fpu.h`
- `architecture/i386/frame.h`

## `odmodule/` (9)

- `odmodule/odconnection.h`
- `odmodule/odconstants.h`
- `odmodule/odcore.h`
- `odmodule/odcredential.h`
- `odmodule/odcstr.h`
- `odmodule/odmodule.h`
- `odmodule/odmoduleconfig.h`
- `odmodule/odrequest.h`
- `odmodule/odtypes.h`

## `pexpert/` (8)

- `pexpert/boot.h`
- `pexpert/i386/boot.h`
- `pexpert/i386/efi.h`
- `pexpert/i386/protos.h`
- `pexpert/machine/boot.h`
- `pexpert/machine/protos.h`
- `pexpert/pexpert.h`
- `pexpert/protos.h`

## `sasl/` (8)

- `sasl/gai.h`
- `sasl/hmac-md5.h`
- `sasl/md5.h`
- `sasl/md5global.h`
- `sasl/prop.h`
- `sasl/sasl.h`
- `sasl/saslplug.h`
- `sasl/saslutil.h`

## `security/` (8)

- `security/audit/audit_ioctl.h`
- `security/openpam.h`
- `security/openpam_attr.h`
- `security/openpam_version.h`
- `security/pam_appl.h`
- `security/pam_constants.h`
- `security/pam_modules.h`
- `security/pam_types.h`

## `servers/` (7)

- `servers/bootstrap.h`
- `servers/bootstrap_defs.h`
- `servers/key_defs.h`
- `servers/ls_defs.h`
- `servers/netname.h`
- `servers/netname_defs.h`
- `servers/nm_defs.h`

## `ffi/` (6)

- `ffi/ffi.h`
- `ffi/ffitarget.h`
- `ffi/ffitarget_arm64.h`
- `ffi/ffitarget_armv7.h`
- `ffi/ffitarget_x86.h`
- `ffi/tramp.h`

## `netinet6/` (6)

- `netinet6/ah.h`
- `netinet6/esp.h`
- `netinet6/in6_var.h`
- `netinet6/ipcomp.h`
- `netinet6/nd6.h`
- `netinet6/raw_ip6.h`

## `EndpointSecurity/` (5)

- `EndpointSecurity/ESClient.h`
- `EndpointSecurity/ESMessage.h`
- `EndpointSecurity/ESMessageCore.h`
- `EndpointSecurity/ESTypes.h`
- `EndpointSecurity/EndpointSecurity.h`

## `os/` (5)

- `os/activity.h`
- `os/arch/arm64.h`
- `os/proc.h`
- `os/signpost.h`
- `os/trace_base.h`

## `bsm/` (4)

- `bsm/audit_filter.h`
- `bsm/audit_session.h`
- `bsm/audit_uevents.h`
- `bsm/libbsm.h`

## `kern/` (4)

- `kern/exc_guard.h`
- `kern/exc_resource.h`
- `kern/kcdata.h`
- `kern/kern_cdata.h`

## `nfs/` (4)

- `nfs/nfs.h`
- `nfs/nfsproto.h`
- `nfs/rpcv2.h`
- `nfs/xdr_subs.h`

## `tidy/` (4)

- `tidy/buffio.h`
- `tidy/platform.h`
- `tidy/tidy.h`
- `tidy/tidyenum.h`

## `gssapi/` (3)

- `gssapi/gssapi.h`
- `gssapi/gssapi_generic.h`
- `gssapi/gssapi_krb5.h`

## `hvf/` (3)

- `hvf/RenderContext.h`
- `hvf/Scaler.h`
- `hvf/Types.h`

## `krb5/` (3)

- `krb5/krb5.h`
- `krb5/locate_plugin.h`
- `krb5/preauth_plugin.h`

## `mach/` (3)

- `mach/arm/asm.h`
- `mach/arm64/asm.h`
- `mach/i386/asm.h`

## `miscfs/` (3)

- `miscfs/devfs/devfs.h`
- `miscfs/specfs/specdev.h`
- `miscfs/union/union.h`

## `arm64/` (2)

- `arm64/hv/hv_kern_types.h`
- `arm64/mte.h`

## `readline/` (2)

- `readline/history.h`
- `readline/readline.h`

## `arm/` (1)

- `arm/cpu_capabilities_public.h`

## `arpa/` (1)

- `arpa/nameser.h`

## `atm/` (1)

- `atm/atm_types.h`

## `bank/` (1)

- `bank/bank_types.h`

## `corpses/` (1)

- `corpses/task_corpse.h`

## `default_pager/` (1)

- `default_pager/default_pager_types.h`

## `device/` (1)

- `device/device_port.h`

## `hfs/` (1)

- `hfs/hfs_mount.h`

## `i386/` (1)

- `i386/user_ldt.h`

## `infiniband/` (1)

- `infiniband/verbs.h`

## `libkern/` (1)

- `libkern/machine/OSByteOrder.h`

## `netkey/` (1)

- `netkey/keysock.h`

## `networkext/` (1)

- `networkext/ne_socket.h`

## `sys/` (1)

- `sys/syscall.h`

## `vfs/` (1)

- `vfs/vfs_support.h`

## `voucher/` (1)

- `voucher/ipc_pthread_priority_types.h`

## `xar/` (1)

- `xar/xar.h`
