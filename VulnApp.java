  import java.sql.*;                                                                           
                                                                                               
  public class VulnApp {                                                                     
      public User getUser(String id) {                                                         
          String query = "SELECT * FROM users WHERE id = " + id;
          return db.execute(query);                                                            
      }                                                                                        
  }                                                                                            
  EOF                                                                                          
            
