// Java cross-language fixture — Clean.java
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class UserService {
    private java.util.Map<String, String> store = new java.util.HashMap<>();

    public boolean authenticate(String username, String password) {
        try {
            String digest = hashPassword(password);
            return lookup(username, digest);
        } catch (Exception e) {
            return false;
        }
    }

    private String hashPassword(String password) throws NoSuchAlgorithmException {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest(password.getBytes());
        StringBuilder sb = new StringBuilder();
        for (byte b : hash) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private boolean lookup(String username, String digest) {
        return digest.equals(store.get(username));
    }
}
