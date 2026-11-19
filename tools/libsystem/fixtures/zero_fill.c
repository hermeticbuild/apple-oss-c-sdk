void clear_bytes(void *buffer, __SIZE_TYPE__ size) {
    __builtin_memset(buffer, 0, size);
}
