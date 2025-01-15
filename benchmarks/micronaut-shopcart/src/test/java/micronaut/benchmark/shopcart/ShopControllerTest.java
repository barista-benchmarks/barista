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

import java.util.regex.Pattern;

import jakarta.inject.Inject;

import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;

import io.micronaut.http.HttpRequest;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.uri.UriBuilder;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import micronaut.benchmark.shopcart.domain.ShoppingCart;

@SuppressWarnings({"rawtypes", "unchecked"})
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@MicronautTest
public class ShopControllerTest {

	@Inject
	EmbeddedServer server;

	@Inject
	@Client("/")
	HttpClient client;

	@Test
	@Order(1)
	void addClient() {
		HttpRequest post = HttpRequest.POST(UriBuilder.of("/").build(), "{ \"username\": \"user0\", \"name\": \"myname\" }");
		String answer = client.toBlocking().retrieve(post);
		assertEquals(answer, new micronaut.benchmark.shopcart.domain.Client("user0", "myname", new ShoppingCart()).toString());
	}

	@Test
	@Order(2)
	void getClient() {
		HttpRequest request = HttpRequest.GET(UriBuilder.of("/").path("user0").build());
		String answer = client.toBlocking().retrieve(request, String.class);
		assertEquals(answer, new micronaut.benchmark.shopcart.domain.Client("user0", "myname", new ShoppingCart()).toString());
	}

	@Test
	@Order(3)
	void getEmptyCart() {
		HttpRequest request = HttpRequest.GET(UriBuilder.of("/cart").path("user0").build());
		String answer = client.toBlocking().retrieve(request, String.class);
		assertEquals(answer, "[]");
	}

	@Test
	@Order(4)
	void addProduct() {
		HttpRequest post = HttpRequest.POST(UriBuilder.of("/cart").build(), "{ \"username\": \"user0\", \"name\": \"Banana\", \"amount\": \"1\" }");
		String answer = client.toBlocking().retrieve(post);
		Pattern p = Pattern.compile("Product = \\{ id = user0\\$0, name = Banana, quantity = 1, timestamp = \\d+, price = Price = \\{ currency = EUR, amount = 1.000000 \\} \\}");
		assert(p.matcher(answer).find());
	}

	@Test
	@Order(5)
	void getCartWithBananas() {
		HttpRequest request = HttpRequest.GET(UriBuilder.of("/cart").path("user0").build());
		String answer = client.toBlocking().retrieve(request, String.class);
		Pattern p = Pattern.compile("\\[Product = \\{ id = user0\\$0, name = Banana, quantity = 1, timestamp = \\d+, price = Price = \\{ currency = EUR, amount = 1.000000 \\} \\}\\]");
		assert(p.matcher(answer).find());
	}

	@Test
	@Order(6)
	void removeBananasFromCart() {
		HttpRequest delete = HttpRequest.DELETE(UriBuilder.of("/cart").build(), "{ \"id\": \"user0$0\", \"username\": \"user0\" }");
		String answer = client.toBlocking().retrieve(delete);
		assertEquals(answer, "user0$0");
	}

	@Test
	@Order(7)
	void getEmptyCartAfterRemovingBananas() {
		HttpRequest request = HttpRequest.GET(UriBuilder.of("/cart").path("user0").build());
		String answer = client.toBlocking().retrieve(request, String.class);
		assertEquals(answer, "[]");
	}

	@Test
	@Order(8)
	void removeClient() {
		HttpRequest delete = HttpRequest.DELETE(UriBuilder.of("/user0").build(), null);
		String answer = client.toBlocking().retrieve(delete);
		assertEquals(answer, "user0");
	}
}
