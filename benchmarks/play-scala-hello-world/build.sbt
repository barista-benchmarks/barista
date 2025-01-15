name := """play-scala-hello-world"""
organization := "com.example"

version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala).enablePlugins(GraalVMNativeImagePlugin)

scalaVersion := "2.13.15"

libraryDependencies += guice
libraryDependencies += "org.scalatestplus.play" %% "scalatestplus-play" % "7.0.1" % Test

assembly / assemblyMergeStrategy := {
  case x if Assembly.isConfigFile(x) =>
  MergeStrategy.concat
  case PathList(ps @ _*) if Assembly.isReadme(ps.last) || Assembly.isLicenseFile(ps.last) =>
  MergeStrategy.rename
  case PathList("META-INF", xs @ _*) =>
  (xs map {_.toLowerCase}) match {
    case ("manifest.mf" :: Nil) | ("index.list" :: Nil) | ("dependencies" :: Nil) =>
    MergeStrategy.discard
    case ps @ (x :: xs) if ps.last.endsWith(".sf") || ps.last.endsWith(".dsa") =>
    MergeStrategy.discard
    case "plexus" :: xs =>
    MergeStrategy.discard
    case "services" :: xs =>
    MergeStrategy.filterDistinctLines
    case ("spring.schemas" :: Nil) | ("spring.handlers" :: Nil) =>
    MergeStrategy.filterDistinctLines
    case _ => MergeStrategy.first
  }
  case _ => MergeStrategy.first
}

PlayKeys.externalizeResources := false

val graalvm_nib_file = settingKey[File]("The full path to the app nib file")
graalvm_nib_file := baseDirectory.value / "target" / (name.value + "-" + version.value + ".nib")

GraalVMNativeImage / graalVMNativeImageOptions ++= Seq(
  s"--bundle-create=${graalvm_nib_file.value},dry-run"
)
