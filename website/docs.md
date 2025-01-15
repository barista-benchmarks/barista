---
layout: mainpage
projectname: Barista
logoname: mona-lisa-round.png
title: Documentation
permalink: /docs.html
---


# Documentation Overview

Thank you for your interest in using the Barista Benchmark Suite!
<br/>
On this page, we provide basic usage instructions, and other useful information.

- [Getting Started with Barista](#getting-started)
- [Contributing to Barista](#contribution-guide)
- [Licensing Information](#licensing)

# <a name="getting-started"></a> Getting Started with Barista

The Barista Benchmark Suite comes with an informative guide
on how to run Barista benchmarks, how to add new benchmarks, run policies and plugins,
and a technical overview of the internal design of the suite.

<div id="readme-holder">
</div>
<script>
loadRemoteContent(
  "readme-holder",
  "https://api.github.com/repos/{{ site.githubOrg }}/{{ site.githubRepo }}/contents/README.md",
  "{{ page.logoname }}",
  "markdown"
)
</script>

The source file that explains how to use Barista can be found
[here](
https://github.com/{{ site.githubOrg }}/{{ site.githubRepo }}/blob/master/README.md
).


# <a name="contribution-guide"></a> Contributing to Barista

One of the aims of the Barista suite is to continually evolve,
and maintain a collection of relevant and interesting benchmarks
for VM, compiler and tool developers.
Barista therefore relies on an open-source contribution process
to derive the set of benchmarks that are useful when optimizing or analyzing the JVM behaviour.
The contribution guide contains detailed information about this process.

<div id="contribution-holder">
</div>
<script>
loadRemoteContent(
  "contribution-holder",
  "https://api.github.com/repos/{{ site.githubOrg }}/{{ site.githubRepo }}/contents/CONTRIBUTING.md",
  "{{ page.logoname }}",
  "markdown"
)
</script>

The source file that explains the contribution process for the Barista suite can be found
[here](
https://github.com/{{ site.githubOrg }}/{{ site.githubRepo }}/blob/master/CONTRIBUTING.md
).


# <a name="licensing"></a> Licensing Information

The Barista Benchmark Suite is available under the Apache 2 license.
