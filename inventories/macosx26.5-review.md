# macOS SDK 26.5 C headers for review

120 SDK paths lack an approved disposition, plus
0 installed headers absent from this SDK.
Probe reach is recorded but does not approve an extra header:
it can itself change __has_include behavior.
An installed path
still needs a source and scope review; a missing path needs a
supported include or omit decision. New SDK paths always need review.

## Root-level (35)

- `AppleTextureEncoder.h` — proposed review
- `NSSystemDirectories.h` — proposed review
- `__libunwind_config.h` — proposed review
- `asl.h` — proposed review
- `bootstrap.h` — proposed review — launchd publishes servers/bootstrap.h, but the SDK also has a distinct root bootstrap.h; its first-party install source is unresolved.
- `cache.h` — proposed review
- `cache_callbacks.h` — proposed review
- `checkint.h` — proposed review
- `dns.h` — proposed review
- `dns_sd.h` — proposed review
- `dns_util.h` — proposed review
- `dtrace.h` — proposed review
- `libmanagedconfigurationfiles.h` — proposed review
- `libunwind.h` — proposed review
- `nameser.h` — proposed review
- `notify.h` — proposed include
- `notify_keys.h` — proposed include
- `profile.h` — proposed review
- `pthread.h` — proposed include
- `pthread_impl.h` — proposed review
- `pthread_spis.h` — proposed review
- `removefile.h` — proposed include
- `resolv.h` — proposed review
- `sched.h` — proposed include
- `slapi-plugin.h` — proposed review
- `string_x86.h` — proposed include
- `sysdir.h` — proposed review
- `timingsafe.h` — proposed include
- `unwind.h` — proposed review — Clang resource overlap
- `unwind_arm_ehabi.h` — proposed review
- `unwind_itanium.h` — proposed review
- `usbuf.h` — proposed review
- `util.h` — proposed include
- `xattr_flags.h` — proposed include
- `xcselect.h` — proposed review

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

## `rpcsvc/` (15)

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
- `rpcsvc/yppasswd.h` — proposed review

## `bsm/` (11)

- `bsm/audit_domain.h` — proposed include
- `bsm/audit_errno.h` — proposed include
- `bsm/audit_fcntl.h` — proposed include
- `bsm/audit_filter.h` — proposed review — Absent from pinned XNU public bsm install list; OpenBSM source evaluation pending.
- `bsm/audit_internal.h` — proposed include
- `bsm/audit_kevents.h` — proposed include
- `bsm/audit_record.h` — proposed include
- `bsm/audit_session.h` — proposed review — Absent from pinned XNU public bsm install list; OpenBSM source evaluation pending.
- `bsm/audit_socket_type.h` — proposed include
- `bsm/audit_uevents.h` — proposed review — Absent from pinned XNU public bsm install list; OpenBSM source evaluation pending.
- `bsm/libbsm.h` — proposed review — Absent from pinned XNU public bsm install list; OpenBSM source evaluation pending.

## `os/` (8)

- `os/activity.h` — proposed review
- `os/arch/arm64.h` — proposed review
- `os/log.h` — proposed review — XNU provides only a kernel-side os/log.h; public user header source remains unresolved.
- `os/proc.h` — proposed review
- `os/security_config.h` — proposed include
- `os/signpost.h` — proposed review
- `os/trace.h` — proposed review — XNU provides only a kernel-side os/trace.h; public user header source remains unresolved.
- `os/trace_base.h` — proposed review

## `mach/` (7)

- `mach/arm/asm.h` — proposed review
- `mach/arm64/asm.h` — proposed review
- `mach/i386/asm.h` — proposed review
- `mach/mach_right.h` — proposed include
- `mach/port_obj.h` — proposed include
- `mach/sync.h` — proposed include
- `mach/vm_task.h` — proposed include

## `security/` (7)

- `security/openpam.h` — proposed review
- `security/openpam_attr.h` — proposed review
- `security/openpam_version.h` — proposed review
- `security/pam_appl.h` — proposed review
- `security/pam_constants.h` — proposed review
- `security/pam_modules.h` — proposed review
- `security/pam_types.h` — proposed review

## `servers/` (5)

- `servers/key_defs.h` — proposed review
- `servers/ls_defs.h` — proposed review
- `servers/netname.h` — proposed review
- `servers/netname_defs.h` — proposed review
- `servers/nm_defs.h` — proposed review

## `pthread/` (4)

- `pthread/introspection.h` — proposed include
- `pthread/pthread_spis.h` — proposed include
- `pthread/spawn.h` — proposed include
- `pthread/stack_np.h` — proposed include

## `libDER/` (2)

- `libDER/DERItem.h` — proposed review
- `libDER/libDER_config.h` — proposed review

## `arm64/` (1)

- `arm64/hv/hv_kern_types.h` — proposed review

## `arpa/` (1)

- `arpa/nameser.h` — proposed review

## `atm/` (1)

- `atm/atm_types.h` — proposed review

## `dispatch/` (1)

- `dispatch/introspection.h` — proposed include

## `infiniband/` (1)

- `infiniband/verbs.h` — proposed review

## `mach_debug/` (1)

- `mach_debug/mach_debug.h` — proposed include

## `networkext/` (1)

- `networkext/ne_socket.h` — proposed review

## `sys/` (1)

- `sys/rbtree.h` — proposed include

## Installation-only headers needing review
