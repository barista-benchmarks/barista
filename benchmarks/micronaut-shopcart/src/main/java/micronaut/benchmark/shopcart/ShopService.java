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
package micronaut.benchmark.shopcart;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.Map;
import java.util.HashMap;

import jakarta.inject.Singleton;

import io.micronaut.cache.annotation.CacheConfig;
import io.micronaut.cache.annotation.CacheInvalidate;
import io.micronaut.cache.annotation.CachePut;
import io.micronaut.cache.annotation.Cacheable;
import micronaut.benchmark.shopcart.domain.Client;
import micronaut.benchmark.shopcart.domain.Price;
import micronaut.benchmark.shopcart.domain.Product;
import micronaut.benchmark.shopcart.domain.ShoppingCart;

@Singleton
@CacheConfig("articles")
public class ShopService {

	private static Map<Integer, Float> prices = new HashMap<Integer,Float>();

	static {
		File file = new File("static-data");
		if(file.exists() && !file.isDirectory()) {
			long start, finish;
			start = System.currentTimeMillis();
			loadPrices(file);
			finish = System.currentTimeMillis();
			System.out.println(String.format("Took %s ms to load static data", finish - start));
		}

	}

	public static void loadPrices(File file) {
		try(BufferedReader br = new BufferedReader(new FileReader(file))) {
			for(String line; (line = br.readLine()) != null; ) {
				String[] splits = line.split(",");
				prices.put(Integer.valueOf(splits[0]), Float.valueOf(splits[1]));
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	@Cacheable
	public Client getClient(String id) {
		return null;
	}

	@CachePut(parameters = {"username"})
	public Client addClient(String username, String name) {
		return new Client(username, name, new ShoppingCart());
	}

	@CachePut(parameters = {"username"})
	public Client addProductToShopCart(String username, Client client, Product product) {
		client.getCart().addProduct(product);
		return client;
	}

	@CachePut(parameters = {"username"})
	public Client removeProductFromShopCart(String username, Client client, Product product) {
		client.getCart().removeProduct(product);
		return client;
	}

	@CacheInvalidate
	public void destroyClient(String username) {
		// Intentionally left empty. This will invalidate the cache entry.
	}

	@Cacheable
	public Product getProduct(String id) {
		return null;
	}

	@CachePut(parameters = {"id"})
	public Product createProduct(String id, String name, Integer amount) {
		Price price = null;
		if (id.chars().allMatch(Character::isDigit)) {
			price = new Price("EUR", Integer.parseInt(id));
		}
		return new Product(id, name, amount, System.currentTimeMillis(), price == null ? new Price("EUR", 1.0f) : price);
	}

	@CacheInvalidate
	public void destroyProduct(String id) { }
}
