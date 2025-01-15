package com.example;

import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.DataOutputStream;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;

/**
 * Unit test for simple App.
 */
public class AppTest {

  /**
   * Rigorous Test :-)
   */
  @Test
  public void testHelloWorldEndpoint() throws IOException {
    String[] args = new String[0];
    App.main(args);

    //Create connection
    URL url = new URL("http://localhost:8010/hello");
    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
    connection.setRequestMethod("GET");

    connection.setRequestProperty("Content-Length", "0");
    connection.setRequestProperty("Content-Language", "en-US");  

    connection.setUseCaches(false);
    connection.setDoOutput(true);

    // //Send request
    DataOutputStream wr = new DataOutputStream (
      connection.getOutputStream());
    wr.close();

    //Get Response  
    InputStream is = connection.getInputStream();
    BufferedReader rd = new BufferedReader(new InputStreamReader(is));
    StringBuilder response = new StringBuilder(); // or StringBuffer if Java version 5+
    String line;
    while ((line = rd.readLine()) != null) {
      response.append(line);
      response.append('\r');
    }
    rd.close();
    String responseContent = response.toString();

    connection.disconnect();

    assertTrue("Hello World!\r".equals(responseContent));
  }
}
