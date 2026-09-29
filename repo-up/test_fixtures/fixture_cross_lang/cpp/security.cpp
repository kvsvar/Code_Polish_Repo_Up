// C++ cross-language fixture — security.cpp
// Intentionally vulnerable for testing purposes.
#include <cstdlib>
#include <cstdio>
#include <openssl/md5.h>
#include <openssl/evp.h>

// Dangerous execution — SEC-DANGEROUS-EXEC
void runCmd(const char* cmd) {
    system(cmd);  // CWE-78
}

void openPipe(const char* cmd) {
    FILE* pipe = popen(cmd, "r");  // CWE-78
    fclose(pipe);
}

// Weak crypto — SEC-WEAK-CRYPTO (OpenSSL)
void hashData(const unsigned char* data, int len, unsigned char* out) {
    EVP_md5();  // SEC-WEAK-CRYPTO
    MD5_Init(nullptr);
}

// Long line — CODE-LONG-LINE
const char* VERY_LONG_CONFIG_STRING_THAT_EXCEEDS_THE_CONFIGURED_LINE_LENGTH_THRESHOLD_OF_ONE_HUNDRED_CHARS = "value";
