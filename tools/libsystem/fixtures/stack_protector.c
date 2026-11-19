int read_stack_slot(unsigned index, int value) {
    volatile unsigned char slots[32];
    index %= sizeof(slots);
    slots[index] = (unsigned char)value;
    return slots[index];
}
