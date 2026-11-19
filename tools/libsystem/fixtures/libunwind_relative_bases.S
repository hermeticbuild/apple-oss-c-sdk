// Darwin exports these compatibility names even though unwind.h marks them
// unavailable. Model the relocations without calling either function.
.data
.quad __Unwind_GetDataRelBase
.quad __Unwind_GetTextRelBase
