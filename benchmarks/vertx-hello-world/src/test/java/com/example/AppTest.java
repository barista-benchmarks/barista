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
import io.vertx.core.Vertx;

public class AppTest {
  @Test
  public void testHelloWorldEndpoint() throws IOException, InterruptedException {
    HTTPVerticle serverVerticle = new HTTPVerticle();
    APIClientVerticle clientVerticle = new APIClientVerticle();
    Vertx.vertx().deployVerticle(serverVerticle);
    Vertx.vertx().deployVerticle(clientVerticle);
    clientVerticle.gotResponse.acquire();

    assertTrue("Hello from Vert.x!".equals(clientVerticle.response));
  }
}
