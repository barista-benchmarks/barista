# Micronaut ShopCart Benchmark

ShopCart is a Micronaut web shopping application.
It exposes endpoints on port 8001 for creating users, filling and querying their shopcart.

## Building The Benchmark

To build the benchmark, run: `mvn package`.

## Building A Standalone Native-Image

To build a standalone executable for the benchmark application, run: `mvn package -Dpackaging=native-image -Denv=dev -Pstandalone`

### Testing The Standalone Application
Running the generated executable should start the Micronaut application:
```
$ ./target/shopcart
 __  __ _                                  _   
|  \/  (_) ___ _ __ ___  _ __   __ _ _   _| |_ 
| |\/| | |/ __| '__/ _ \| '_ \ / _` | | | | __|
| |  | | | (__| | | (_) | | | | (_| | |_| | |_ 
|_|  |_|_|\___|_|  \___/|_| |_|\__,_|\__,_|\__|
15:42:17.438 [main] INFO  io.micronaut.runtime.Micronaut - Startup completed in 6ms. Server Running: http://localhost:8001
```

To quickly validate the application you can use `curl` and hit some end-points:

#### Add A New User:
```bash
curl --header "Content-Type: application/json" \
  --request POST --data '{"username":"1234","name":"John Barista"}' \
  http://localhost:8001/
```
Expected response:
```
Client = { username = 1234, name = John Barista, cart = ShoppingCart = { nextProductId = 0, numberProducts = 0 } }
```

#### Assign Items To User:
```bash
curl --header "Content-Type: application/json" \
  --request POST --data '{"username":"1234","name":"coffee", "amount":"10"}' \
  http://localhost:8001/cart
```
Expected response:
```
Product = { id = 1234$0, name = coffee, quantity = 10, timestamp = 1760449181607, price = Price = { currency = EUR, amount = 1.000000 } }
```

#### Read Cart For User:
```bash
curl --header "Content-Type: application/json" \
  --request GET http://localhost:8001/cart/1234
```
Expected response:
```
[Product = { id = 1234$0, name = coffee, quantity = 10, timestamp = 1760449181607, price = Price = { currency = EUR, amount = 1.000000 } }]
```
## Building A Layered Native-Image

First, to build the _base layer_, run: `mvn install -Dpackaging=native-image -Denv=dev -Pbase-layer`.
This builds the project and installs the base layer jar that the app layer build depends on. 
Then it creates a base layer archive `base-layer-target/shopcart-base-layer.nil` and a shared library `base-layer-target/libshopcartbaselayer.so`.
The layer archive is used by the app layer as a build time dependency.
The shared library is used by the app layer executable as a run time dependency.

Then, to build the _app layer_, run: `mvn package -Dpackaging=native-image -Denv=dev -Papp-layer`.
This will create the native executable in `app-layer-target/shopcart-layered`.

### Testing The Layered Application

The app layer requires that the base layer shared library is placed next to it at run time.
Run and test the layered application:

```
$ cp base-layer-target/libshopcartbaselayer.so app-layer-target
$ ./app-layer-target/shopcart-layered
 __  __ _                                  _   
|  \/  (_) ___ _ __ ___  _ __   __ _ _   _| |_ 
| |\/| | |/ __| '__/ _ \| '_ \ / _` | | | | __|
| |  | | | (__| | | (_) | | | | (_| | |_| | |_ 
|_|  |_|_|\___|_|  \___/|_| |_|\__,_|\__,_|\__|
19:02:33.059 [main] INFO  io.micronaut.runtime.Micronaut - Startup completed in 46ms. Server Running: http://localhost:8001

```