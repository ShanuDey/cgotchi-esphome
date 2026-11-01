#pragma once
// String helpers. No ESPHome includes, so they build and test on a PC (tests/).

#include <cctype>
#include <string>
#include <vector>

namespace cgotchi {
namespace ui {

// Word-wraps to `width` characters; a word longer than a line (a URL) is split.
inline std::vector<std::string> wrap_text(const std::string &text, size_t width) {
  std::vector<std::string> lines;
  if (width == 0) return lines;
  std::string word, line;
  for (size_t i = 0; i <= text.size(); i++) {
    const char c = i < text.size() ? text[i] : ' ';
    if (c != ' ') {
      word += c;
      continue;
    }
    if (word.empty()) continue;
    while (word.size() > width) {
      if (!line.empty()) {
        lines.push_back(line);
        line.clear();
      }
      lines.push_back(word.substr(0, width));
      word.erase(0, width);
    }
    if (!line.empty() && line.size() + 1 + word.size() > width) {
      lines.push_back(line);
      line = word;
    } else {
      line += (line.empty() ? "" : " ");
      line += word;
    }
    word.clear();
  }
  if (!line.empty()) lines.push_back(line);
  return lines;
}

// Splits on newlines and drops empty lines.
inline std::vector<std::string> split_lines(const std::string &text) {
  std::vector<std::string> lines;
  size_t start = 0;
  while (start < text.size()) {
    size_t end = text.find('\n', start);
    if (end == std::string::npos) end = text.size();
    if (end > start) lines.push_back(text.substr(start, end - start));
    start = end + 1;
  }
  return lines;
}

// Percent-encodes all but URL-safe characters, for use in a query string.
inline std::string percent_encode(const std::string &text) {
  static const char *HEX = "0123456789ABCDEF";
  std::string out;
  for (unsigned char c : text) {
    if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
      out += (char) c;
    } else {
      out += '%';
      out += HEX[c >> 4];
      out += HEX[c & 15];
    }
  }
  return out;
}

// Snapshot address: a bundled page by name, or "Custom" for any URL.
inline std::string frame_request_url(const std::string &server, const std::string &source,
                                     const std::string &custom_url) {
  if (source != "Custom") return server + "/frame.jpg?page=" + source;
  return server + "/frame.jpg?url=" + percent_encode(custom_url);
}

}  // namespace ui
}  // namespace cgotchi
