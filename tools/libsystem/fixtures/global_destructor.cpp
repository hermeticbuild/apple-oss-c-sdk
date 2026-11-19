volatile int destroyed;
struct Object {
    ~Object() { destroyed = 1; }
};
Object global_object;
