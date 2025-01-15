package com.example;

import info.debatty.java.stringsimilarity.redux.Cosine;
import info.debatty.java.stringsimilarity.redux.Jaccard;
import info.debatty.java.stringsimilarity.redux.QGram;
import info.debatty.java.stringsimilarity.redux.SorensenDice;
import info.debatty.java.stringsimilarity.redux.SzymkiewiczSimpson;
import info.debatty.java.stringsimilarity.redux.Tversky;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

public class SimilarityMetrics {
  static class Tuple {
    final int first;
    final int second;

    Tuple(int first, int second) {
      this.first = first;
      this.second = second;
    }

    @Override
    public boolean equals(Object o) {
      if (this == o) return true;
      if (o == null || getClass() != o.getClass()) {
        return false;
      }
      Tuple tuple = (Tuple) o;
      return (first == tuple.first && second == tuple.second) ||
        (first == tuple.second && second == tuple.first);
    }

    @Override
    public int hashCode() {
      return (first ^ second) * 0x9e3775cd;
    }

    @Override
    public String toString() {
      return "(" + first + ", " + second + ")";
    }
  }

  static List<Map<String, Integer>> profiles(String[] texts) {
    var profiles = new ArrayList<Map<String, Integer>>();
    for (String text : texts) {
      var c = new Cosine();
      var profile = c.getProfile(text);
      profiles.add(profile);
    }
    return profiles;
  }

  static List<String> pairsByQgram(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::qgram);
  }

  static List<String> pairsByCosine(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::cosine);
  }

  static List<String> pairsBySorensenDice(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::sorensenDice);
  }

  public static List<String> pairsByJaccard(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::jaccard);
  }

  public static List<String> pairsByTversky(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::tversky);
  }

  public static List<String> pairsBySzymkiewiczSimpson(List<Map<String, Integer>> textProfiles) {
    return pairsByDistance(textProfiles, SimilarityMetrics::szymkiewiczSimpson);
  }

  static List<String> pairsByDistance(List<Map<String, Integer>> texts, BiFunction<Map<String, Integer>, Map<String, Integer>, Double> distance) {
    Map<Tuple, Double> similarities = new HashMap<>();

    for (int i = 0; i < texts.size(); i++) {
      for (int j = i + 1; j < texts.size(); j++) {
        var key = new Tuple(i, j);
        var text1 = texts.get(i);
        var text2 = texts.get(j);
        var d = distance.apply(text1, text2);
        similarities.put(key, d);
      }
    }

    return similarities.entrySet().stream().sorted((x, y) -> {
      var xv = x.getValue();
      var yv = y.getValue();
      if (xv < yv) {
        return -1;
      } else if (xv > yv) {
        return 1;
      } else {
        return 0;
      }
    }).map(e -> e.getKey() + " -> " + e.getValue()).collect(Collectors.toList());
  }

  private static double qgram(Map<String, Integer> text1, Map<String, Integer> text2) {
    var qgram = new QGram(3);
    var distance = qgram.distance(text1, text2);
    return distance;
  }

  private static double cosine(Map<String, Integer> text1, Map<String, Integer> text2) {
    var cosine = new Cosine(3);
    var distance = cosine.similarity(text1, text2);
    return distance;
  }

  private static double sorensenDice(Map<String, Integer> text1, Map<String, Integer> text2) {
    var sorensenDice = new SorensenDice(3);
    var distance = sorensenDice.similarity(text1, text2);
    return distance;
  }

  private static double jaccard(Map<String, Integer> text1, Map<String, Integer> text2) {
    var jaccard = new Jaccard(3);
    var distance = jaccard.similarity(text1, text2);
    return distance;
  }

  private static double tversky(Map<String, Integer> text1, Map<String, Integer> text2) {
    var tversky = new Tversky(3);
    var distance = tversky.similarity(text1, text2);
    return distance;
  }

  private static double szymkiewiczSimpson(Map<String, Integer> text1, Map<String, Integer> text2) {
    var szymkiewiczSimpson = new SzymkiewiczSimpson(3);
    var distance = szymkiewiczSimpson.similarity(text1, text2);
    return distance;
  }
}
