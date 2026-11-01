#include "phone_time.h"
#include "esphome/core/log.h"
#include "esphome/core/string_ref.h"

namespace esphome::phone_time {

static const char *const TAG = "phone_time";

void PhoneTime::setup() { this->base_->add_handler(this); }

void PhoneTime::dump_config() { ESP_LOGCONFIG(TAG, "Phone time page: /time"); }

bool PhoneTime::canHandle(AsyncWebServerRequest *request) const {
  if (request->method() != HTTP_GET)
    return false;
  char url_buf[AsyncWebServerRequest::URL_BUF_SIZE];
  StringRef url = request->url_to(url_buf);
  return url == ESPHOME_F("/time");
}

void PhoneTime::handleRequest(AsyncWebServerRequest *request) {
  request->send(200, ESPHOME_F("text/html"), this->page_);
}

}  // namespace esphome::phone_time
