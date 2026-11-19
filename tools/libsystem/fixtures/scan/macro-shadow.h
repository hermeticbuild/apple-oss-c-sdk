extern int scan_shadowed(void);
extern int scan_replacement(void);

#define scan_shadowed scan_replacement
