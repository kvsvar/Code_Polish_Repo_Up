package com.example;
public class Dangerous {
    public void run(String cmd) throws Exception {
        Runtime.getRuntime().exec(cmd);
    }
}
