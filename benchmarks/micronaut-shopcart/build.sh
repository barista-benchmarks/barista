#!/usr/bin/env bash
# Copyright 2020-2021 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euxo pipefail
if [ $# -gt 0 ] && [ $1 = "--help" ]; then
  echo -e "Builds the project jar and then uses GraalVM to generate a nib file (Native Image Bundle)\n\nusage: build.sh [--help] [--skip-nib-generation] [--get-jar] [--get-nib] [--maven-options=MAVEN_OPTIONS]\n\noptions:\n\t--help\t\t\t\tshows this help message and exits\n\t--skip-nib-generation\t\tskips building the application nib (Native Image Bundle) file, only builds the jar\n\t--get-jar\t\t\tprints the path of the built jar without building anything. The path will be printed in the pattern of 'application jar file path is: <path>\\\n'\n\t--get-nib\t\t\tprints the path of the built nib (Native Image Bundle) file without building anything. The path will be printed in the pattern of 'application nib file path is: <path>\\\n'\n\t--maven-options=MAVEN_OPTIONS\tadditional options to pass to mvn when building maven projects"
  exit 0
fi;
DIR="$( cd -P "$( dirname "${BASH_SOURCE}" )" && pwd )"
VERSION=0.3.10
JAR="$DIR/target/shopcart-$VERSION.jar"
NIB="$DIR/target/shopcart-$VERSION.nib"
if [ $# -gt 0 ] && [ $1 = "--get-jar" ]; then
  echo "application jar file path is: $JAR"
  exit 0
fi;
if [ $# -gt 0 ] && [ $1 = "--get-nib" ]; then
  echo "application nib file path is: $NIB"
  exit 0
fi;
maven_options=""
for arg in "$@"
do
  if [[ $arg == --maven-options=* ]]; then
    maven_options="${arg#--maven-options=}"
  fi
done
"$DIR/mvnw" package -f "$DIR/pom.xml" $maven_options
if [ $# -gt 0 ] && [ $1 = "--skip-nib-generation" ]; then
  exit 0
fi;
"$DIR/mvnw" package -Dpackaging=native-image -f "$DIR/pom.xml" $maven_options
"$DIR/mvnw" install -Dpackaging=native-image -f "$DIR/pom.xml" $maven_options
