// Unit tests for text.h. Plain C++17, no ESPHome:  g++ -std=c++17 -I.. test_text.cpp -o test_text && ./test_text
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "../text.h"

using cgotchi::ui::frame_request_url;
using cgotchi::ui::percent_encode;
using cgotchi::ui::split_lines;
using cgotchi::ui::wrap_text;
using Lines = std::vector<std::string>;

static int failures = 0;

static void expect(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

int main() {
  expect(wrap_text("", 18).empty(), "empty text has no lines");
  expect(wrap_text("   ", 18).empty(), "only spaces has no lines");
  expect(wrap_text("hello world", 18) == Lines{"hello world"}, "short text stays on one line");
  expect(wrap_text("aaaa bbbb cccc", 9) == (Lines{"aaaa bbbb", "cccc"}), "wraps at the width");
  expect(wrap_text("aaaa bbbb", 9) == Lines{"aaaa bbbb"}, "a line of exactly the width fits");
  expect(wrap_text("aaaaaaaaaaaa", 5) == (Lines{"aaaaa", "aaaaa", "aa"}), "a long word is split");
  expect(wrap_text("hi aaaaaaa", 5) == (Lines{"hi", "aaaaa", "aa"}), "a long word starts its own line");
  expect(wrap_text("a   b", 18) == Lines{"a b"}, "repeated spaces collapse");
  expect(wrap_text("abc", 0).empty(), "a width of 0 gives no lines instead of looping");

  expect(split_lines("a\nb\n\nc") == (Lines{"a", "b", "c"}), "split_lines drops empty lines");
  expect(split_lines("").empty(), "split_lines of nothing");
  expect(split_lines("clock") == Lines{"clock"}, "split_lines without a newline");

  expect(percent_encode("abc-_.~123") == "abc-_.~123", "safe characters stay");
  expect(percent_encode("a b/c") == "a%20b%2Fc", "space and slash are encoded");
  expect(percent_encode("http://x:8123/p?q=1") == "http%3A%2F%2Fx%3A8123%2Fp%3Fq%3D1", "a URL is encoded");

  expect(frame_request_url("http://s:1", "clock", "ignored") == "http://s:1/frame.jpg?page=clock", "bundled page");
  expect(frame_request_url("http://s:1", "Custom", "http://a/b") == "http://s:1/frame.jpg?url=http%3A%2F%2Fa%2Fb",
         "custom url is encoded");

  if (failures == 0) std::printf("all passed\n");
  return failures == 0 ? 0 : 1;
}
