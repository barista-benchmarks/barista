# Spring Petclinic Benchmark

The Spring Petclinic benchmark is based on the Petclinic sources located on [github](https://github.com/spring-projects/spring-petclinic).
Newer Spring Petclinic versions (starting from Spring Boot 3) should work out of the box.
The directory `spring-petclinic-sources` contains a cleaned up version of the repository that contains only the maven wrapper, `pom.xml` and the `src` directory from the original repository.

## Updating Petclinic To A Newer Version

Clone the petclinic github repository and checkout the `main` branch.
Remove everything from the directory except:
 - `mvnw`
 - `mvnw.cmd`
 - `.mvn`
 - `pom.xml`
 - `src`
Modify the `pom.xml` to enable a dry build of bundles.
Currently, this can be done by adding the following to the `pom.xml`:
```
      <plugin>
        <groupId>org.graalvm.buildtools</groupId>
        <artifactId>native-maven-plugin</artifactId>
        <version>0.9.21</version>
        <configuration>
          <metadataRepository>
              <enabled>true</enabled>
              <version>0.2.6</version>
          </metadataRepository>
          <buildArgs>
            <buildArg>--bundle-create=${project.build.directory}/spring-petclinic-${project.version}.nib</buildArg>
            <buildArg>--dry-run</buildArg>
          </buildArgs>
        </configuration>
      </plugin>
```
Note that the metadata repository version and the native build tools version may change, and you may not need to explicitly set them.

Ensure you have a GraalVM installation with the latest native-image on your PATH, and then run the `package-mx.sh` script to create the required mx libraries from the newer petclinic sources.
