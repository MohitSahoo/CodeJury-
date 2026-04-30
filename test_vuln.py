  import subprocess                                                                            
  import sqlite3
  import os                                                                                    
                                                            
  def sql_injection_vuln(username, password):                                                  
      # SQL injection vulnerability                                                            
      query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"     
      conn = sqlite3.connect('database.db')                 
      cursor = conn.cursor()                                                                   
      cursor.execute(query)
      return cursor.fetchone()                                                                 
                                                            
  def command_injection_vuln(user_file):                                                       
      # Command injection vulnerability                     
      os.system(f"cat /var/log/{user_file}")                                                 
      subprocess.call(f"grep error {user_file}", shell=True)
                                                                                               
  def path_traversal_vuln(filename):
      # Path traversal vulnerability                                                           
      with open(f"/uploads/{filename}", 'r') as f:          
          return f.read()                                                                      
  EOF 
