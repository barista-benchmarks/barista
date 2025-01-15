package com.example;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.Vertx;

public class HTTPVerticle extends AbstractVerticle {

  @Override
  public void start() {
    long startTimestamp = System.nanoTime();
    vertx.createHttpServer().requestHandler(req -> {
      req.response()
        .putHeader("content-type", "text/plain")
        .end("Hello from Vert.x!");
    }).listen(8011, listen -> {
      if (listen.succeeded()) {
        long runningTimestamp = System.nanoTime();
        double startupTime = (runningTimestamp - startTimestamp) / 1E6;
        System.out.printf("Server listening on http://localhost:8011/ after %.2fms!\n", startupTime);
      } else {
        listen.cause().printStackTrace();
        System.exit(1);
      }
    });
  }

  public static void main(String[] args) {
    Vertx.vertx().deployVerticle(new HTTPVerticle());
  }
}