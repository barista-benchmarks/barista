# Spring Boot Hello World Benchmark

This benchmark exposes a simple `/hello` GET endpoint that returns `Hello, World!`.
The skeleton from this benchmark is generated from https://start.spring.io/, by including the `GraalVM Native Support` and the `Spring Web` dependencies.

# Updating The Benchmark

Create a new template using the Spring Initializer linked above.
Copy the template's `pom.xml` to the existing project's `pom.xml` and update it's configuration to create bundles instead of building a native-image.
Currently, you can do that by adding the following:
```
<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <version>0.9.21</version>
    <configuration>
        <buildArgs>
            <buildArg>--bundle-create=${project.build.directory}/spring-hello-world-${project.version}.nib</buildArg>
            <buildArg>--dry-run</buildArg>
        </buildArgs>
    </configuration>
</plugin>
```

Note that you may not need to specify the exact build tools version this block in the future.

Ensure you have a GraalVM installation with the latest native-image on your PATH, and then run the `package-mx.sh` script to create the required mx libraries from the newer petclinic sources.

