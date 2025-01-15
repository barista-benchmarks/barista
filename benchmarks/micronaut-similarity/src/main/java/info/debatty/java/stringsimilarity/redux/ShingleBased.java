/*
 * The MIT License
 *
 * Copyright 2015 Thibault Debatty.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package info.debatty.java.stringsimilarity.redux;

import net.jcip.annotations.Immutable;

import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

/**
 * Abstract class for string similarities that rely on set operations (like
 * cosine similarity or jaccard index).
 * <p>
 * k-shingling is the operation of transforming a string (or text document) into
 * a set of n-grams, which can be used to measure the similarity between two
 * strings or documents.
 * <p>
 * Generally speaking, a k-gram is any sequence of k tokens. We use here the
 * definition from Leskovec, Rajaraman &amp; Ullman (2014), "Mining of Massive
 * Datasets", Cambridge University Press: Multiple subsequent spaces are
 * replaced by a single space, and a k-gram is a sequence of k characters.
 * <p>
 * Default value of k is 3. A good rule of thumb is to imagine that there are
 * only 20 characters and estimate the number of k-shingles as 20^k. For small
 * documents like e-mails, k = 5 is a recommended value. For large documents,
 * such as research articles, k = 9 is considered a safe choice.
 *
 * @author Thibault Debatty
 */
@Immutable
public abstract class ShingleBased {

  private static final int DEFAULT_K = 3;

  private final int k;
  private final HashMap<String, String> shingleCache;

  /**
   * @param k
   * @throws IllegalArgumentException if k is &lt;= 0
   */
  public ShingleBased(final int k) {
    if (k <= 0) {
      throw new IllegalArgumentException("k should be positive!");
    }
    this.k = k;
    this.shingleCache = new HashMap<>();
  }

  /**
   *
   */
  ShingleBased() {
    this(DEFAULT_K);
  }

  /**
   * Return k, the length of k-shingles (aka n-grams).
   *
   * @return The length of k-shingles.
   */
  public final int getK() {
    return k;
  }

  /**
   * Compute and return the profile of s, as defined by Ukkonen "Approximate
   * string-matching with q-grams and maximal matches".
   * https://www.cs.helsinki.fi/u/ukkonen/TCS92.pdf The profile is the number
   * of occurrences of k-shingles, and is used to compute q-gram similarity,
   * Jaccard index, etc. Pay attention: the memory requirement of the profile
   * can be up to k * size of the string
   *
   * @param string
   * @return the profile of this string, as an unmodifiable Map
   */
  public final Map<String, Integer> getProfile(final String string) {
    final HashMap<String, Count> shingles = new HashMap<>();

    String string_no_space = string.replace(" ", "");
    for (int i = 0; i < (string_no_space.length() - k + 1); i++) {
      String shingle = cached(string_no_space.substring(i, i + k));
      Count count = shingles.get(shingle);
      if (count != null) {
        count.increment();
      } else {
        count = new Count(1);
        shingles.put(shingle, count);
      }
    }

    return new Map<>() {
      @Override
      public int size() {
        return shingles.size();
      }

      @Override
      public boolean isEmpty() {
        return shingles.isEmpty();
      }

      @Override
      public boolean containsKey(Object key) {
        return shingles.containsKey(key);
      }

      @Override
      public boolean containsValue(Object value) {
        return shingles.containsValue(value);
      }

      @Override
      public Integer get(Object key) {
        var count = shingles.get(key);
        return count == null ? 0 : count.get();
      }

      @Override
      public Integer put(String key, Integer value) {
        throw new UnsupportedOperationException();
      }

      @Override
      public Integer remove(Object key) {
        throw new UnsupportedOperationException();
      }

      @Override
      public void putAll(Map<? extends String, ? extends Integer> m) {
        throw new UnsupportedOperationException();
      }

      @Override
      public void clear() {
        throw new UnsupportedOperationException();
      }

      @Override
      public Set<String> keySet() {
        return shingles.keySet();
      }

      @Override
      public Collection<Integer> values() {
        throw new UnsupportedOperationException();
      }

      @Override
      public Set<Entry<String, Integer>> entrySet() {
        var entries = shingles.entrySet();
        return new Set<Entry<String, Integer>>() {
          @Override
          public int size() {
            return entries.size();
          }

          @Override
          public boolean isEmpty() {
            return entries.isEmpty();
          }

          @Override
          public boolean contains(Object o) {
            throw new UnsupportedOperationException();
          }

          @Override
          public Iterator<Entry<String, Integer>> iterator() {
            var iterator = entries.iterator();
            return new Iterator<Entry<String, Integer>>() {
              @Override
              public boolean hasNext() {
                return iterator.hasNext();
              }

              @Override
              public Entry<String, Integer> next() {
                var entry = iterator.next();
                return new Entry<String, Integer>() {
                  @Override
                  public String getKey() {
                    return entry.getKey();
                  }

                  @Override
                  public Integer getValue() {
                    return entry.getValue().get();
                  }

                  @Override
                  public Integer setValue(Integer value) {
                    throw new UnsupportedOperationException();
                  }
                };
              }
            };
          }

          @Override
          public Object[] toArray() {
            throw new UnsupportedOperationException();
          }

          @Override
          public <T> T[] toArray(T[] a) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean add(Entry<String, Integer> stringIntegerEntry) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean remove(Object o) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean containsAll(Collection<?> c) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean addAll(Collection<? extends Entry<String, Integer>> c) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean retainAll(Collection<?> c) {
            throw new UnsupportedOperationException();
          }

          @Override
          public boolean removeAll(Collection<?> c) {
            throw new UnsupportedOperationException();
          }

          @Override
          public void clear() {
            throw new UnsupportedOperationException();
          }
        };
      }
    };
  }

  private String cached(String s) {
    var existing = shingleCache.get(s);
    if (existing != null) {
      return existing;
    }
    shingleCache.put(s, s);
    return s;
  }

  public static class Count {
    private int i;

    public Count(int i) {
      this.i = i;
    }

    public int get() {
      return i;
    }

    public void increment() {
      i++;
    }
  }
}