package com.example;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.net.InetSocketAddress;

/**
 * Hello world!
 */
public class App {
  public static void main(String[] args) throws IOException {
    long startTimestamp = System.nanoTime();

    HttpServer server = HttpServer.create(new InetSocketAddress(8010), 0);
    server.createContext("/hello", new HelloWorldHandler());
    server.setExecutor(null);
    server.start();

    long runningTimestamp = System.nanoTime();
    double startupTime = (runningTimestamp - startTimestamp) / 1E6;
    System.out.printf("Basic Hello-World HttpServer started after %.2fms!\n", startupTime);
  }
}
