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

import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;

import jakarta.validation.Valid;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Delete;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import micronaut.benchmark.shopcart.command.ClientSaveCommand;
import micronaut.benchmark.shopcart.command.ProductDeleteCommand;
import micronaut.benchmark.shopcart.command.ProductSaveCommand;
import micronaut.benchmark.shopcart.domain.Client;
import micronaut.benchmark.shopcart.domain.Product;
import micronaut.benchmark.shopcart.domain.ShoppingCart;
import io.micronaut.serde.annotation.SerdeImport;

@Controller
@SerdeImport(ProductSaveCommand.class)
public class ShopController {

	private final ShopService shopService;

	protected static AtomicInteger clientCount = new AtomicInteger(0);

	public ShopController(ShopService shopService) {
		this.shopService = shopService;
	}

	@Post
	public String addClient(@Body @Valid ClientSaveCommand cmd) {
		int ccount = clientCount.incrementAndGet();

		if (cmd.getUsername() == null) {
			cmd.setUsername(String.format("client%d", ccount));
		}

		Client client = shopService.addClient(cmd.getUsername(), cmd.getName());

		if (client == null) {
			return String.format("Error, unable to create client: %s", cmd);
		}

		return client.toString();
	}

	@Get("/{cid}")
	public String getClient(String cid) {
		Client client = shopService.getClient(cid);
		if (client != null) {
			return client.toString();
		} else {
			return String.format("Error, no such client: %s", cid);
		}
	}

	@Delete("/{cid}")
	public String removeClient(String cid) {
		Client client = shopService.getClient(cid);

		if (client == null) {
			return cid;
		}

		ShoppingCart cart = client.getCart();
		for (int i = 0; i < cart.getNextProductId(); i++) {
			shopService.destroyProduct(cid + "$" + i);
		}
		shopService.destroyClient(cid);
		return cid;
	}

	@Post("/cart")
	public String addProduct(@Body @Valid ProductSaveCommand cmd) {
		Client client = shopService.getClient(cmd.getUsername());

		if (client == null) {
			return String.format("Error, no such client: %s", cmd);
		}

		ShoppingCart cart = client.getCart();
		Product product = shopService.createProduct(cmd.getUsername() + "$" + cart.getNextProductId(), cmd.getName(), cmd.getAmount());

		if (product == null) {
			return String.format("Error, unable to create product: %s", cmd);
		}

		shopService.addProductToShopCart(client.getUsername(), client, product);
		return product.toString();
	}

	@Get("/cart/{cid}")
	public String getProducts(String cid) {
		Client client = shopService.getClient(cid);

		if (client == null) {
			return String.format("Error, no such client: %s", cid);
		}

		ShoppingCart cart = client.getCart();
		Product[] products = new Product[cart.getNumberProducts()];
		for (int found = 0, i = 0; i < products.length; i++) {
			Product product = shopService.getProduct(cid + "$" + i);
			if (product != null) {
				products[found++] = product;
			}
		}
		return Arrays.toString(products);
	}

	@Delete("/cart")
	public String removeProduct(@Body @Valid ProductDeleteCommand cmd) {
		Client client = shopService.getClient(cmd.getUsername());

		if (client == null) {
			return String.format("Error, no such client: %s", cmd);
		}

		Product product = shopService.getProduct(cmd.getId());

		if (product == null) {
			return String.format("Error, unable to find product: %s", cmd);
		}

		client.getCart().removeProduct(product);

		shopService.destroyProduct(cmd.getId());

		return cmd.getId();
	}

	@Get("/memory")
	public Long memory() {
		System.gc();
		long bytes = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
		return bytes / 1024;
	}
}
