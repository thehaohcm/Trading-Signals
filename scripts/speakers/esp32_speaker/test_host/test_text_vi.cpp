// Test trên máy tính: g++ -std=c++17 -I../src test_text_vi.cpp ../src/text_vi.cpp -o t && ./t < cases.txt
#include <iostream>
#include <string>
#include "text_vi.h"
int main() {
    std::string title, msg;
    while (std::getline(std::cin, title) && std::getline(std::cin, msg)) {
        std::cout << textvi::toSpeechText(title, msg) << "\n";
        for (auto& c : textvi::splitChunks(textvi::toSpeechText(title, msg), 60)) std::cout << "  | " << c << "\n";
        std::cout << "  D: " << textvi::cleanForDisplay(title) << "\n";
    }
}
