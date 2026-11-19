/* Client of the exact public link spelling in libplatform's alias list. */
extern void platform_clear(void *, __SIZE_TYPE__) __asm("___bzero");

void clear_with_platform_alias(void *buffer, __SIZE_TYPE__ size) {
    platform_clear(buffer, size);
}
