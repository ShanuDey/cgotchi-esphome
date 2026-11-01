#pragma once

#include "esphome/core/component.h"
#include "esphome/components/web_server_base/web_server_base.h"

namespace esphome::phone_time {

class PhoneTime : public AsyncWebHandler, public Component {
 public:
  explicit PhoneTime(web_server_base::WebServerBase *base) : base_(base) {}

  void set_page(const char *page) { this->page_ = page; }
  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::WIFI; }

  bool canHandle(AsyncWebServerRequest *request) const override;
  void handleRequest(AsyncWebServerRequest *request) override;

 protected:
  web_server_base::WebServerBase *base_;
  const char *page_{""};
};

}  // namespace esphome::phone_time
