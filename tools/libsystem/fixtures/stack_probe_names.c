// Link-only probe. The actual stack-check functions use a special calling convention.
void compiler_rt_probe(void) __asm("___chkstk_darwin");
void pthread_probe(void) __asm("____chkstk_darwin");

void request_both_stack_probes(void) {
    compiler_rt_probe();
    pthread_probe();
}
