#include <libunwind.h>
#include <unwind.h>

#define REFERENCE(symbol) __attribute__((used)) static __typeof__(&symbol) ref_##symbol = &symbol

REFERENCE(_Unwind_Backtrace);
REFERENCE(_Unwind_DeleteException);
REFERENCE(_Unwind_FindEnclosingFunction);
REFERENCE(_Unwind_Find_FDE);
REFERENCE(_Unwind_ForcedUnwind);
REFERENCE(_Unwind_GetCFA);
REFERENCE(_Unwind_GetGR);
REFERENCE(_Unwind_GetIP);
REFERENCE(_Unwind_GetIPInfo);
REFERENCE(_Unwind_GetLanguageSpecificData);
REFERENCE(_Unwind_GetRegionStart);
REFERENCE(_Unwind_RaiseException);
REFERENCE(_Unwind_Resume);
REFERENCE(_Unwind_Resume_or_Rethrow);
REFERENCE(_Unwind_SetGR);
REFERENCE(_Unwind_SetIP);
REFERENCE(__deregister_frame);
REFERENCE(__register_frame);

REFERENCE(unw_get_fpreg);
REFERENCE(unw_get_proc_info);
REFERENCE(unw_get_proc_name);
REFERENCE(unw_get_reg);
REFERENCE(unw_getcontext);
REFERENCE(unw_init_local);
REFERENCE(unw_is_fpreg);
REFERENCE(unw_is_signal_frame);
REFERENCE(unw_local_addr_space);
REFERENCE(unw_regname);
REFERENCE(unw_resume);
REFERENCE(unw_set_fpreg);
REFERENCE(unw_set_reg);
REFERENCE(unw_step);
