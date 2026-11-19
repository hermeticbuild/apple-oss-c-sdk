static _Thread_local volatile int sequence;

int main(void) {
    return ++sequence == 1 ? 0 : 1;
}
