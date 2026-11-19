static volatile int cleaned;

struct Cleanup {
    ~Cleanup() { ++cleaned; }
};

__attribute__((noinline)) void throw_through_cleanup(int code)
{
    Cleanup cleanup;
    throw code;
}

int main(int argc, char **)
{
    try {
        throw_through_cleanup(argc);
    } catch (int code) {
        return code != argc || cleaned != 1;
    }
    return 1;
}
