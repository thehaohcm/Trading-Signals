#include "text_vi.h"

#include <algorithm>
#include <cstdint>

namespace textvi {

typedef std::u32string U;

// ───────────────────────── UTF-8 <-> code point ─────────────────────────

static U decode(const std::string& s) {
    U out;
    out.reserve(s.size());
    size_t i = 0;
    while (i < s.size()) {
        uint8_t c = (uint8_t)s[i];
        char32_t cp;
        int extra;
        if (c < 0x80) { cp = c; extra = 0; }
        else if ((c & 0xE0) == 0xC0) { cp = c & 0x1F; extra = 1; }
        else if ((c & 0xF0) == 0xE0) { cp = c & 0x0F; extra = 2; }
        else if ((c & 0xF8) == 0xF0) { cp = c & 0x07; extra = 3; }
        else { i++; continue; }  // byte lỗi → bỏ
        bool ok = true;
        for (int k = 1; k <= extra; k++) {
            if (i + k >= s.size() || (((uint8_t)s[i + k]) & 0xC0) != 0x80) { ok = false; break; }
            cp = (cp << 6) | (((uint8_t)s[i + k]) & 0x3F);
        }
        if (!ok) { i++; continue; }
        out.push_back(cp);
        i += extra + 1;
    }
    return out;
}

static std::string encode(const U& u) {
    std::string out;
    out.reserve(u.size() * 2);
    for (char32_t cp : u) {
        if (cp < 0x80) out.push_back((char)cp);
        else if (cp < 0x800) { out.push_back((char)(0xC0 | (cp >> 6))); out.push_back((char)(0x80 | (cp & 0x3F))); }
        else if (cp < 0x10000) {
            out.push_back((char)(0xE0 | (cp >> 12))); out.push_back((char)(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back((char)(0x80 | (cp & 0x3F)));
        } else {
            out.push_back((char)(0xF0 | (cp >> 18))); out.push_back((char)(0x80 | ((cp >> 12) & 0x3F)));
            out.push_back((char)(0x80 | ((cp >> 6) & 0x3F))); out.push_back((char)(0x80 | (cp & 0x3F)));
        }
    }
    return out;
}

static U lit(const char* s) { return decode(std::string(s)); }

size_t utf8Length(const std::string& s) { return decode(s).size(); }

// ───────────────────────── phân loại ký tự ─────────────────────────

static bool isDigit(char32_t c) { return c >= '0' && c <= '9'; }
static bool isAsciiUpper(char32_t c) { return c >= 'A' && c <= 'Z'; }
static bool isAsciiAlnum(char32_t c) { return isDigit(c) || (c >= 'a' && c <= 'z') || isAsciiUpper(c); }
// "Chữ" theo nghĩa \w của Python: chữ ASCII, số, '_' và chữ có dấu (Latin mở rộng)
static bool isWord(char32_t c) {
    return isAsciiAlnum(c) || c == '_' || (c >= 0xC0 && c <= 0x24F && c != 0xD7 && c != 0xF7) ||
           (c >= 0x1E00 && c <= 0x1EFF);
}
static bool isSpace(char32_t c) { return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == 0xA0; }

static bool isEmoji(char32_t c) {
    return (c >= 0x1F000 && c <= 0x1FAFF) || (c >= 0x2600 && c <= 0x27BF) || c == 0xFE0F || c == 0x200D ||
           (c >= 0x2B00 && c <= 0x2BFF) || (c >= 0x25A0 && c <= 0x25FF);
}

static char32_t toLower(char32_t c) {
    if (isAsciiUpper(c)) return c + 32;
    if (c >= 0xC0 && c <= 0xDE && c != 0xD7) return c + 32;
    if (c == 0x1A0 || c == 0x1AF) return c + 1;                                  // Ơ Ư
    if (((c >= 0x100 && c <= 0x17F) || (c >= 0x1EA0 && c <= 0x1EFF)) && (c % 2 == 0)) return c + 1;  // Đ Ả Ạ ...
    return c;
}

static bool endsWith(const U& s, const U& suf) {
    return s.size() >= suf.size() && std::equal(suf.begin(), suf.end(), s.end() - suf.size());
}

static void replaceAll(U& s, const U& from, const U& to) {
    if (from.empty()) return;
    size_t pos = 0;
    while ((pos = s.find(from, pos)) != U::npos) {
        s.replace(pos, from.size(), to);
        pos += to.size();
    }
}

// ───────────────────────── tiêu đề trùng nội dung ─────────────────────────

static std::vector<U> words(const U& s) {
    std::vector<U> w;
    U cur;
    for (char32_t c : s) {
        if (isWord(c)) cur.push_back(toLower(c));
        else if (!cur.empty()) { w.push_back(cur); cur.clear(); }
    }
    if (!cur.empty()) w.push_back(cur);
    return w;
}

static bool titleIsRedundant(const U& title, const U& message) {
    std::vector<U> tw = words(title);
    if (tw.empty()) return true;
    std::vector<U> mw = words(message);
    size_t hit = 0;
    for (const U& w : tw)
        if (std::find(mw.begin(), mw.end(), w) != mw.end()) hit++;
    return hit * 10 >= tw.size() * 7;  // ≥ 70% từ của tiêu đề đã có trong nội dung
}

// ───────────────────────── số → cách đọc tiếng Việt ─────────────────────────

// "1,234.56" → "1234 phẩy 56" ; "52,500" → "52500" ; "0.870" → "0 phẩy 87" ; dạng khác giữ nguyên.
static U formatNumber(const U& tok) {
    size_t dot = tok.find(U'.');
    U intPart = tok.substr(0, dot);
    U decPart = dot == U::npos ? U() : tok.substr(dot + 1);
    if (decPart.find(U'.') != U::npos || decPart.find(U',') != U::npos) return tok;  // "1.2.3" → giữ nguyên
    if (intPart.find(U',') != U::npos) {
        // phải đúng nhóm nghìn: nhóm đầu 1-3 chữ số, các nhóm sau đúng 3 chữ số
        std::vector<U> groups(1);
        for (char32_t c : intPart) {
            if (c == U',') groups.emplace_back();
            else groups.back().push_back(c);
        }
        if (groups[0].empty() || groups[0].size() > 3) return tok;
        for (size_t g = 1; g < groups.size(); g++)
            if (groups[g].size() != 3) return tok;
        U clean;
        for (const U& g : groups) clean += g;
        intPart = clean;
    } else if (dot == U::npos) {
        return tok;  // số nguyên thường
    }
    while (!decPart.empty() && decPart.back() == U'0') decPart.pop_back();
    if (decPart.empty()) return intPart;
    return intPart + lit(" phẩy ") + decPart;
}

static U processNumbers(const U& in) {
    U out;
    size_t i = 0, n = in.size();
    while (i < n) {
        char32_t c = in[i];
        bool startNum = isDigit(c) && (i == 0 || !(isDigit(in[i - 1])));
        if (!startNum) {
            out.push_back(c);
            i++;
            continue;
        }
        // Đọc token số: [\d.,]* kết thúc bằng chữ số
        size_t j = i;
        while (j < n && (isDigit(in[j]) || in[j] == U'.' || in[j] == U',')) j++;
        while (j > i && !isDigit(in[j - 1])) j--;
        U tok = in.substr(i, j - i);

        // Dấu âm / dương đứng trước: "-55.44" → "âm 55.44" (không áp cho "BTC-5", "1.-2")
        if (!out.empty() && (out.back() == U'-' || out.back() == U'+')) {
            char32_t before = out.size() >= 2 ? out[out.size() - 2] : U' ';
            if (!isWord(before) && before != U'.') {
                bool neg = out.back() == U'-';
                out.pop_back();
                if (neg) out += lit("âm ");
            }
        }
        // "$617.42" → "617.42 đô la"
        bool dollar = false;
        {
            size_t k = out.size();
            while (k > 0 && isSpace(out[k - 1])) k--;
            if (k > 0 && out[k - 1] == U'$') {
                out.erase(k - 1);
                dollar = true;
            }
        }
        bool afterLan = endsWith(out, lit("lần ")) || endsWith(out, lit("Lần ")) || endsWith(out, lit("LẦN "));

        out += formatNumber(tok);
        i = j;

        // Hậu tố: $, %, đ (đứng riêng)
        size_t k = i;
        while (k < n && isSpace(in[k])) k++;
        if (k < n && in[k] == U'$') {
            out += lit(" đô la");
            i = k + 1;
            dollar = false;
        } else if (k < n && in[k] == U'%') {
            out += lit(" phần trăm");
            i = k + 1;
        } else if (k < n && in[k] == 0x111 /* đ */ && (k + 1 >= n || !isWord(in[k + 1]))) {
            out += lit(" đồng");
            i = k + 1;
        } else if (afterLan && i + 1 < n && in[i] == U'/' && isDigit(in[i + 1])) {
            out += lit(" trên ");  // "lần 2/3" → "lần 2 trên 3"
            i += 1;
        }
        if (dollar) out += lit(" đô la");
    }
    return out;
}

// ───────────────────────── mã giao dịch ─────────────────────────

static U processTickers(const U& in) {
    static const char* suffixes[] = {"USDT", "USDC", "BUSD", "FDUSD"};
    U out;
    size_t i = 0, n = in.size();
    while (i < n) {
        if (!isWord(in[i])) { out.push_back(in[i]); i++; continue; }
        size_t j = i;
        while (j < n && isWord(in[j])) j++;
        U w = in.substr(i, j - i);
        // "BINANCE:BTCUSDT" → "BTCUSDT"
        bool allUpper = !w.empty() && std::all_of(w.begin(), w.end(), [](char32_t c) { return isAsciiUpper(c); });
        if (allUpper && j + 1 < n && in[j] == U':' && (isAsciiUpper(in[j + 1]) || isDigit(in[j + 1]))) {
            i = j + 1;
            continue;
        }
        bool upperAlnum = std::all_of(w.begin(), w.end(), [](char32_t c) { return isAsciiUpper(c) || isDigit(c); });
        if (upperAlnum) {
            for (const char* s : suffixes) {
                U suf = lit(s);
                if (w.size() > suf.size() && endsWith(w, suf)) {
                    size_t base = w.size() - suf.size();
                    if (base >= 2 && base <= 10) {
                        w = w.substr(0, base) + U(1, U' ') + suf;
                    }
                    break;
                }
            }
        }
        out += w;
        i = j;
    }
    return out;
}

// ───────────────────────── dọn khoảng trắng / dấu câu ─────────────────────────

static bool isPunct(char32_t c) { return c == U'.' || c == U',' || c == U':' || c == U';' || c == U'!' || c == U'?'; }

static U tidy(const U& in) {
    // gộp khoảng trắng
    U a;
    for (char32_t c : in) {
        if (isSpace(c)) {
            if (!a.empty() && a.back() != U' ') a.push_back(U' ');
        } else a.push_back(c);
    }
    // bỏ khoảng trắng trước dấu câu
    U b;
    for (char32_t c : a) {
        if (isPunct(c) && !b.empty() && b.back() == U' ') b.pop_back();
        b.push_back(c);
    }
    // gộp chuỗi dấu ". , ;" liên tiếp (giữ dấu đầu), không áp cho "!" "?"
    U d;
    for (size_t i = 0; i < b.size(); i++) {
        char32_t c = b[i];
        bool soft = c == U'.' || c == U',' || c == U':' || c == U';';
        if (soft) {
            // bỏ qua nếu ký tự (không tính khoảng trắng) trước đó cũng là dấu mềm
            size_t k = d.size();
            while (k > 0 && d[k - 1] == U' ') k--;
            if (k > 0 && (d[k - 1] == U'.' || d[k - 1] == U',' || d[k - 1] == U':' || d[k - 1] == U';')) {
                d.erase(k);
                d.push_back(U' ');
                continue;
            }
        }
        d.push_back(c);
    }
    // lại gộp khoảng trắng do bước trên
    U e;
    for (char32_t c : d) {
        if (c == U' ' && !e.empty() && e.back() == U' ') continue;
        e.push_back(c);
    }
    // trim " .,:;"
    auto trimChar = [](char32_t c) { return c == U' ' || c == U'.' || c == U',' || c == U':' || c == U';'; };
    size_t s = 0, t = e.size();
    while (s < t && trimChar(e[s])) s++;
    while (t > s && trimChar(e[t - 1])) t--;
    return e.substr(s, t - s);
}

// ───────────────────────── API ─────────────────────────

std::string toSpeechText(const std::string& titleIn, const std::string& messageIn, size_t maxChars) {
    U title = tidy(decode(titleIn)), message = tidy(decode(messageIn));
    U text;
    if (!title.empty() && !message.empty() && !titleIsRedundant(title, message)) text = title + lit(". ") + message;
    else text = message.empty() ? title : message;

    replaceAll(text, lit("➔"), lit(" sang "));
    replaceAll(text, lit("→"), lit(" sang "));
    replaceAll(text, lit("|"), lit(", "));
    U t;
    for (char32_t c : text) {
        if (isEmoji(c)) { t.push_back(U' '); continue; }
        switch (c) {
            case U'[': case U']': case U'(': case U')': case U'{': case U'}':
            case U'<': case U'>': case U'*': case U'_': case U'#': case U'`': case U'~':
                t.push_back(U' ');
                break;
            default: t.push_back(c);
        }
    }
    t = processNumbers(t);
    replaceAll(t, lit("$"), lit(" đô la "));
    t = processTickers(t);
    replaceAll(t, lit(" - "), lit(", "));
    replaceAll(t, lit("—"), lit(", "));
    replaceAll(t, lit("–"), lit(", "));
    t = tidy(t);
    if (t.size() > maxChars) {
        U cut = t.substr(0, maxChars);
        size_t sp = cut.rfind(U' ');
        t = sp == U::npos ? cut : cut.substr(0, sp);
        t = tidy(t);
    }
    return encode(t);
}

std::vector<std::string> splitChunks(const std::string& textIn, size_t maxChars) {
    std::vector<std::string> chunks;
    U text = decode(textIn);
    U cur;
    size_t i = 0;
    while (i < text.size()) {
        size_t j = i;
        while (j < text.size() && text[j] != U' ') j++;
        U w = text.substr(i, j - i);
        if (w.size() > maxChars) w = w.substr(0, maxChars);
        if (!cur.empty() && cur.size() + 1 + w.size() > maxChars) {
            chunks.push_back(encode(cur));
            cur.clear();
        }
        if (!cur.empty()) cur.push_back(U' ');
        cur += w;
        // Ngắt ở cuối câu nếu đoạn đã khá dài → giọng đọc tự nhiên hơn
        if (!cur.empty() && (cur.back() == U'.' || cur.back() == U'!' || cur.back() == U'?') && cur.size() >= maxChars / 2) {
            chunks.push_back(encode(cur));
            cur.clear();
        }
        i = j + 1;
    }
    if (!cur.empty()) chunks.push_back(encode(cur));
    return chunks;
}

std::string cleanForDisplay(const std::string& s) {
    U in = decode(s), out;
    for (char32_t c : in) {
        if (isEmoji(c) || c == U'[' || c == U']' || c == U'*' || c == U'_' || c == U'`') { out.push_back(U' '); continue; }
        if (c > 0xFFFF) continue;  // font OLED không có ký tự ngoài BMP
        out.push_back(c);
    }
    // gộp khoảng trắng + trim
    U r;
    for (char32_t c : out) {
        if (isSpace(c)) { if (!r.empty() && r.back() != U' ') r.push_back(U' '); }
        else {
            if (isPunct(c) && !r.empty() && r.back() == U' ') r.pop_back();
            r.push_back(c);
        }
    }
    while (!r.empty() && r.back() == U' ') r.pop_back();
    size_t st = 0;
    while (st < r.size() && (r[st] == U' ' || r[st] == U':')) st++;
    return encode(r.substr(st));
}

std::string urlEncode(const std::string& s) {
    static const char* hex = "0123456789ABCDEF";
    std::string out;
    for (unsigned char ch : s) {
        if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '-' || ch == '_' ||
            ch == '.' || ch == '~') {
            out.push_back((char)ch);
        } else {
            out.push_back('%');
            out.push_back(hex[ch >> 4]);
            out.push_back(hex[ch & 15]);
        }
    }
    return out;
}

}  // namespace textvi
