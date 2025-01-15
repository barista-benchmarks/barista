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

public class ShoppingCart {

	private int nextProductId;
	private int numberProducts;

	public ShoppingCart() {
		this.nextProductId = 0;
		this.numberProducts = 0;
	}

	public int getNextProductId() {
		return nextProductId;
	}

	public int getNumberProducts() {
		return numberProducts;
	}

	public void addProduct(Product product) {
		this.nextProductId += 1;
		this.numberProducts += 1;
	}

	public void removeProduct(Product product) {
		this.numberProducts -= 1;
	}

	@Override
	public String toString() {
		return String.format("ShoppingCart = { nextProductId = %s, numberProducts = %s }", nextProductId, numberProducts);
	}
}
