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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

import jakarta.inject.Inject;

import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;

import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import micronaut.benchmark.shopcart.domain.Client;
import micronaut.benchmark.shopcart.domain.Product;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@MicronautTest
class ShopServiceTest {

	@Inject
	ShopService shopService;

	@Test
	@Order(1)
	public void notFoundClient() {
		Client client = shopService.getClient("user1");
		assertNull(client);
	}

	@Test
	@Order(2)
	public void createClient() {
		Client client = shopService.addClient("user1", "User Name");
		assertNotNull(client);
		assertEquals(client.getName(), "User Name");
		assertEquals(client.getUsername(), "user1");
		assertEquals(client.getCart().getNextProductId(), 0);
		assertEquals(client.getCart().getNumberProducts(), 0);
	}

	@Test
	@Order(3)
	public void foundClient() {
		Client client = shopService.getClient("user1");
		assertNotNull(client);
		assertEquals(client.getName(), "User Name");
		assertEquals(client.getUsername(), "user1");
		assertEquals(client.getCart().getNextProductId(), 0);
		assertEquals(client.getCart().getNumberProducts(), 0);
	}

	@Test
	@Order(4)
	public void notFoundProduct() {
		Product product = shopService.getProduct("user1$0");
		assertNull(product);
	}

	@Test
	@Order(5)
	public void createProduct() {
		Product product = shopService.createProduct("user1$0", "Banana", 1);
		assertNotNull(product);
		assertEquals(product.getName(), "Banana");
		assertEquals(product.getQuantity(), 1);
	}

	@Test
	@Order(6)
	public void foundProduct() {
		Product product = shopService.getProduct("user1$0");
		assertNotNull(product);
		assertEquals(product.getName(), "Banana");
		assertEquals(product.getQuantity(), 1);
	}

	@Test
	@Order(7)
	public void addProduct() {
		Client client = shopService.getClient("user1");
		Product product = shopService.getProduct("user1$0");
		client = shopService.addProductToShopCart(client.getUsername(), client, product);
		assertEquals(client.getCart().getNextProductId(), 1);
		assertEquals(client.getCart().getNumberProducts(), 1);
	}

	@Test
	@Order(8)
	public void removeProduct() {
		Client client = shopService.getClient("user1");
		Product product = shopService.getProduct("user1$0");
		client = shopService.removeProductFromShopCart("user1$0", client, product);
		assertEquals(client.getCart().getNumberProducts(), 0);
		assertEquals(client.getCart().getNextProductId(), 1);
	}

	@Test
	@Order(9)
	public void destroyProduct() {
		shopService.destroyProduct("user1$0");
		Product product = shopService.getProduct("user1$0");
		assertNull(product);
	}

	@Test
	@Order(10)
	public void destroyClient() {
		shopService.destroyClient("user1");
		Client client = shopService.getClient("user1");
		assertNull(client);
	}
}
