package com.demo.utils;
public class ConfigLoader {
    public void load(String cmd) throws Exception {
        Runtime.getRuntime().exec(cmd);
    }
}
