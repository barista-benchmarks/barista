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
package micronaut.benchmark.shopcart.domain;

public class Product {

	final private String id;
	final private String name;
	final private int quantity;
	final private Long timestamp;
	final private Price price;

	public Product(String id, String name, int quantity, Long timestamp, Price price) {
		this.id = id;
		this.name = name;
		this.quantity = quantity;
		this.timestamp = timestamp;
		this.price = price;
	}

	public String getId() {
		return id;
	}

	public String getName() {
		return name;
	}

	public int getQuantity() {
		return quantity;
	}

	public Long getTimestamp() {
		return timestamp;
	}

	public Price getPrice() {
		return price;
	}

	@Override
	public String toString() {
		return String.format("Product = { id = %s, name = %s, quantity = %d, timestamp = %s, price = %s }", id, name, quantity, timestamp, price);
	}

}
