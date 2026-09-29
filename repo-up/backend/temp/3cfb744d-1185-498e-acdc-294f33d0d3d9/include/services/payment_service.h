#ifndef PAY_SVC_H
#define PAY_SVC_H
#include "notification_service.h"
#include <curl/curl.h>
class PaymentService { public: void pay() { curl_easy_init(); } };
#endif
