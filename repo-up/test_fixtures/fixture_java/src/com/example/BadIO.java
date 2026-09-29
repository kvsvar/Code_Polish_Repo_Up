package com.example;
import java.net.URL;
public class BadIO {
    public void fetch() throws Exception {
        new URL("http://test.com").openConnection();
    }
}
