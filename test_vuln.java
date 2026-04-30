import java.sql.*;

public class UserLogin {
    public void login(String username, String password) throws SQLException {
        Connection conn = DriverManager.getConnection("jdbc:mysql://localhost/db", "root", "pass");
        // SQL Injection
        String query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(query);
    }

    public void runCommand(String cmd) throws Exception {
        // Command Injection
        Runtime.getRuntime().exec(cmd);
    }
}
