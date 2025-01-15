
plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.ktor)
    id("org.graalvm.buildtools.native") version "0.10.3"
}

group = "com.example"
version = "0.0.1"

application {
    mainClass.set("io.ktor.server.netty.EngineMain")

    val isDevelopment: Boolean = project.ext.has("development")
    applicationDefaultJvmArgs = listOf("-Dio.ktor.development=$isDevelopment")
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.logback.classic)
    implementation(libs.ktor.server.config.yaml)
    testImplementation(libs.ktor.server.test.host)
    testImplementation(libs.kotlin.test.junit)
}

tasks.withType<JavaCompile> {
    val javaVersion = JavaVersion.current().majorVersion.toInt()

    // Only set source/target compatibility for Java 24 and above
    if (javaVersion >= 24) {
        sourceCompatibility = "23"
        targetCompatibility = "23"
    }
}

graalvmNative {
    binaries.all {
        resources.autodetect()
    }
    binaries {
        named("main") {
            buildArgs.add("--bundle-create=${project.buildDir}/ktor-hello-world-${project.version}.nib,dry-run")
        }
    }
}
