#ifndef LIBSYSTEM_EXAMPLE_H
#define LIBSYSTEM_EXAMPLE_H

int example_call(void);
extern int example_value;
extern _Thread_local int example_thread;
static inline int example_inline(void) { return 7; }

#endif
