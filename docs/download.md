---
layout: mainpage
projectname: Barista
logoname: mona-lisa-round.png
title: Downloads
permalink: /download.html
---


# Download

This webpage contains a list of all Barista releases.
More information on each release can be found at the [GitHub release page](https://github.com/{{ site.githubOrg }}/{{ site.githubRepo }}/releases).

<div id="releases-holder">
</div>

<script>
getReleaseList("releases-holder", "https://api.github.com/repos/{{ site.githubOrg }}/{{ site.githubRepo }}/releases")
</script>

<br /><br />
