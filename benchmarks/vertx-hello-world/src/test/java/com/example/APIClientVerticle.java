package com.example;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.buffer.Buffer;
import io.vertx.ext.web.client.HttpResponse;
import io.vertx.ext.web.client.WebClient;
import io.vertx.ext.web.client.WebClientOptions;
import java.util.concurrent.Semaphore;

public class APIClientVerticle extends AbstractVerticle {

  public String response;
  public Semaphore gotResponse = new Semaphore(0);

  @Override
  public void start() {
    WebClient client = WebClient.create(vertx, new WebClientOptions());

    client
      .get(8011, "localhost", "/")
      .putHeader("Accept", "text/plain")
      .send(ar -> {
        if (ar.succeeded()) {
          HttpResponse<Buffer> response = ar.result();
          String responseContent = response.body().toString("ISO-8859-1");
          System.out.println("Got HTTP response with status " + response.statusCode() + " with data "
              + responseContent);
          this.response = responseContent;
          this.gotResponse.release();
        } else {
          ar.cause().printStackTrace();
        }

        // Submit our API request and then exit (to make testing easier)
        getVertx().close();
    });
  }
}