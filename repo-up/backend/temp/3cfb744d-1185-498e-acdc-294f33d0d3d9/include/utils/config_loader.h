#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H
#include <cstdlib>
class ConfigLoader { public: void load() { system("cat config"); } };
#endif
