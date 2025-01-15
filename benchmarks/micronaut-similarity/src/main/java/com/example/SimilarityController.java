/*
 * Copyright 2020-2021 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.example;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.Produces;
import io.micronaut.serde.annotation.Serdeable;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Serdeable
class Request {
  String[] texts;

  Request(String[] texts) {
    this.texts = texts;
  }
}

@Controller("/similarity")
public class SimilarityController {

  @Post(value = "/order", consumes = MediaType.APPLICATION_JSON)
  @Produces(MediaType.APPLICATION_JSON)
  public HttpResponse<Map<String, Object>> get(@Body Request req) {
    var start = System.nanoTime();
    if (req.texts == null) {
      return HttpResponse.badRequest(new HashMap<>() {{
        put("error", "Request has no 'texts' field!");
      }});
    }
    var profiles = SimilarityMetrics.profiles(req.texts);
    List<String> qgram = SimilarityMetrics.pairsByQgram(profiles);
    List<String> cosine = SimilarityMetrics.pairsByCosine(profiles);
    List<String> sorensenDice = SimilarityMetrics.pairsBySorensenDice(profiles);
    List<String> jaccard = SimilarityMetrics.pairsByJaccard(profiles);
    List<String> tversky = SimilarityMetrics.pairsByTversky(profiles);
    List<String> szymkiewiczSimpson = SimilarityMetrics.pairsBySzymkiewiczSimpson(profiles);
    var time = System.nanoTime() - start;

    return HttpResponse.ok(new HashMap<>() {{
      put("qgram", qgram);
      put("cosine", cosine);
      put("sorensenDice", sorensenDice);
      put("jaccard", jaccard);
      put("tversky", tversky);
      put("szymkiewiczSimpson", szymkiewiczSimpson);
      put("time", time);
    }});
  }

    @Get
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> get() {
        return HttpResponse.ok(new HashMap<>());
    }
}
