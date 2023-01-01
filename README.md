# SciStag

### A stack of helpful libraries & applications for the rapid development of data driven solutions.

```
                                      (  (  )   (  )   )
                                       `(  `(     )'  )'
                                         `--(_   _)--'
                                              \-/
                                             /oO \
                                            /..   \
                                            `--'.  \              .             
                                                 \   `.__________/)
```

---

Build Status
------------

[![PyPi Version](https://img.shields.io/pypi/v/SciStag.svg)](https://pypi.python.org/pypi/SciStag)
![](https://shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue)
[![Documentation Status](https://readthedocs.org/projects/scistag/badge/?version=latest)](https://scistag.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://coveralls.io/repos/github/SciStag/SciStag/badge.svg?branch=main)](https://coveralls.io/github/SciStag/SciStag)
[![Pylint](https://raw.githubusercontent.com/SciStag/SciStag/main/docs/source/generated/pylint.svg)](https://coveralls.io/github/SciStag/SciStag)

[![Ubuntu Unittests Status](https://github.com/scistag/scistag/workflows/Ubuntu%20Unittests/badge.svg)](https://github.com/scistag/scistag/actions?query=workflow%3A%22Ubuntu+Unittests%22)
[![Windows Unittests Status](https://github.com/scistag/scistag/workflows/Windows%20Unittests/badge.svg)](https://github.com/scistag/scistag/actions?query=workflow%3A%22Windows+Unittests%22)

* SciStag is available on pypi: https://pypi.python.org/pypi/SciStag
* The source is hosted on GitHub: https://github.com/SciStag/SciStag
* The documentation is available on ReadTheDocs: https://scistag.readthedocs.io/

---

This project is still under heavy development and in a very early stage -
feel free to experiment with the modules and examples which are already
provided.

The goal of **SciStag** is to bundle the strengths of the many small, awesome
Python technologies from OpenCV via Flask to Pandas and enable users to combine
these libraries and build awesome data driven solutions with a minimum amount of
code.

SciStag currently consists of the following so called **stags**:

<table>
<tr><td><b>VisualLog</b></td>
<td>Allows the dynamic creation of documentation in HTML, Markdown and text format
and the fast data evaluation through its built-in in-place reload of Python
modules so you can quickly and efficiently dive into and browse through your 
data, evaluate different parameters quickly etc.
</td></tr>
<tr><td><b>ImageStag</b></td>
<td>Image analysis and modification made easy by combining the strengths of PILLOW, OpenCV and SKImage.
</td>
</tr>
<tr><td><b>MediaStag</b></td>
<td>Easy integration of streaming media data such as videos into your solution.</td>
</tr>
<tr><td><b>DataStag</b></td>
<td>Low-latency inter-container and -process exchange of image and other binary data for Computer Vision and other data
  intensive microservice architectures.</td></tr>
<tr><td><b>RemoteStag</b></td>
<td>Remote and asynchronous task execution - such as a neural network inference</td>
</tr>
<tr><td><b>WebStag</b></td>
<td>Helpful tools for accessing, processing web data and the easy provision
of Python components as local microservices.</td></tr>
<tr><td><b>FileStag</b>
</td>
<td>
Tools for handling for large amount of files in a data engineering process 
such as easy scanning and handling data in an Azure Storage.
</td></tr>
</table>

---

## Setup

SciStag comes completely bundled with all required standard components.

`pip install scistag[full]` or when using poetry `poetry add scistag[full]` and
you are ready to go! :)

If you do not want to install advanced components such as Kivy you are also fine
with a more light-weighted

`pip install scistag[logstag,flask]`

## Getting started

You can already find several cool
demos [here](https://github.com/SciStag/SciStag/tree/main/scistag/examples) on
GitHub.

The most advanced and central component of SciStag is currently definitely **
VisualLog** which
lets you create log data and documentation very efficiently with a Jupyter-like
feeling but without loosing all the awesome code editing features of your
IDEs such as Visual Studio Code or PyCharm.

You can find the demos for **VisualLog** in the [
vislog](https://github.com/SciStag/SciStag/tree/main/scistag/examples/vislog)
examples folder.

## License

Copyright (c) 2022-present Michael Ikemann.

Released under the terms of the **MIT License**.

### Third-party data

The SciStag module on PyPi is bundled with the following data:

* The [Roboto](https://fonts.google.com/specimen/Roboto) font - licensed and
  distributed under the terms of
  the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
  .
* The [Roboto Flex](https://github.com/googlefonts/roboto-flex) font - licensed
  under
  the [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web)
* The [JetBrains Mono](https://www.jetbrains.com/lp/mono/) font - licensed under
  the [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web)
  .
* [Iconic font](https://github.com/Templarian/MaterialDesign-Webfont) by the
  Material Design Icons community covered
  by [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web)
* Emojis and country flags from
  the [Noto Emoji](https://github.com/googlefonts/noto-emoji) project. Tools and
  most
  image resources are under
  the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
  .
    * Flag images under the public domain or otherwise exempt from copyright.
* The emoji unicode character name mappings and details are based upon the
  unicode data files, Copyright © 1991-2022
  Unicode, Inc, licensed under the terms of
  the [UNICODE, INC. LICENSE AGREEMENT](https://www.unicode.org/license.txt)

### Third-party source code

* Contains portions of code from [imkgit](https://github.com/jarrekk/imgkit),
  Copyright (C) 2016 Cory Dolphin, Olin
  College, released under the terms of the **MIT License**.

## Contributors

SciStag is developed by Michael Ikemann / [@Alyxion](https://github.com/Alyxion)
. - Feel free to reach out to me
via [LinkedIn](https://www.linkedin.com/in/michael-ikemann/).

## Thanks

Big thanks go out to the following people and institutions for their direct or 
indirect support:
* [Zühlke Engineering](https://zuehlke.com/) for all
  the support over the last 4 years, the awesome culture and letting me form the future with you.
* [Shree Nayar](http://www.cs.columbia.edu/~nayar/) for his outstanding in-depth guides and papers in the area of Computer Vision
* [Joseph Zimmerman](https://www.smashingmagazine.com/author/joseph-zimmerman/) - for his JavaScript guides
* ... and all I have forgotten ;)