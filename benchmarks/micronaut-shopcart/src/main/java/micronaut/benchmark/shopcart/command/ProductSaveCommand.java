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
package micronaut.benchmark.shopcart.command;

import jakarta.validation.constraints.NotBlank;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class ProductSaveCommand {

	@NotBlank
	private String username;

	@NotBlank
	private String name;

	@NotBlank
	private Integer amount;

	public ProductSaveCommand() { }
	public ProductSaveCommand(String username, String name, Integer amount) {
		this.username = username;
		this.name = name;
		this.amount = amount;
	}

	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public String getName() {
		return name;
	}

	public void setName(String id) {
		this.name = id;
	}

	public Integer getAmount() {
		return amount;
	}

	public void setAmount(Integer amount) {
		this.amount = amount;
	}

	@Override
	public String toString() {
		return String.format("ProductSaveCommand = { username = %s, name = %s, amount = %s }", username, name, amount);
	}
}
