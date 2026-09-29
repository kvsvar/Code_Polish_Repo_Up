// C++ cross-language fixture — clean.cpp
// Clean: proper class, try/catch, no weak crypto calls.
#include <iostream>
#include <string>
#include <stdexcept>

class UserService {
public:
    UserService() {}

    bool authenticate(const std::string& username, const std::string& password) {
        try {
            return lookup(username, password);
        } catch (const std::exception& e) {
            return false;
        }
    }

    void addUser(const std::string& username, const std::string& password) {
        store[username] = password;
    }

private:
    std::map<std::string, std::string> store;

    bool lookup(const std::string& username, const std::string& password) {
        auto it = store.find(username);
        if (it == store.end()) return false;
        return it->second == password;
    }
};
