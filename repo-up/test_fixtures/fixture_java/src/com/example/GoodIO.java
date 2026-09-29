package com.example;
import java.io.File;
public class GoodIO {
    public void read() {
        try {
            new java.io.FileInputStream(new File("test.txt"));
        } catch(Exception e) {}
    }
}
