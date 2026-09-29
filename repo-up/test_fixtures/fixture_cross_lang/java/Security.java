// Java cross-language fixture — Security.java
import java.security.MessageDigest;
import java.io.FileInputStream;
import java.io.ObjectInputStream;

public class Security {

    // Weak crypto — SEC-WEAK-CRYPTO
    public String hashIt(String data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] hash = md.digest(data.getBytes());
        return new String(hash);
    }

    // Dangerous execution — SEC-DANGEROUS-EXEC
    public void runCmd(String cmd) throws Exception {
        Runtime.getRuntime().exec(cmd);
    }

    // Unsafe deserialization — SEC-CWE-502
    public Object deserialize(String path) throws Exception {
        FileInputStream fis = new FileInputStream(path);
        ObjectInputStream ois = new ObjectInputStream(fis);
        return ois.readObject();
    }

    // Missing exception handling — SEC-CWE-703
    public Object readFile(String path) throws Exception {
        FileInputStream fis = new FileInputStream(path);
        return fis;
    }

    // Fake secret — SEC-HARDCODED-SECRET (FAKE value)
    private static final String FAKE_KEY = "api_key = 'x7kP9mNqR2wL5vB8tH3jE6yF1cA4dG0'";
}
