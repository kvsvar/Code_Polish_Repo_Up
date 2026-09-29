#include <fstream>
void read() {
    try {
        std::ifstream f("test.txt");
    } catch(...) {}
}
