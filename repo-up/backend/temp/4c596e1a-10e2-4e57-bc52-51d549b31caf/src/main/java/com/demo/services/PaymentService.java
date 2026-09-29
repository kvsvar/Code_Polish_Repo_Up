package com.demo.services;
import java.net.HttpURLConnection;
import java.net.URL;
import com.demo.config.Constants;
public class PaymentService {
  NotificationService ns;
  public void pay() throws Exception {
    HttpURLConnection conn = (HttpURLConnection) new URL("http://api").openConnection();
  }
}
