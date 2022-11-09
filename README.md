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
[![Documentation Status](https://readthedocs.org/projects/scistag/badge/?version=latest)](https://scistag.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://coveralls.io/repos/github/SciStag/SciStag/badge.svg?branch=main)](https://coveralls.io/github/SciStag/SciStag)
[![Pylint](https://raw.githubusercontent.com/SciStag/SciStag/v0.0.3/docs/source/generated/pylint.svg)](https://coveralls.io/github/SciStag/SciStag)

[![Ubuntu Unittests Status](https://github.com/scistag/scistag/workflows/Ubuntu%20Unittests/badge.svg)](https://github.com/scistag/scistag/actions?query=workflow%3A%22Ubuntu+Unittests%22)

* SciStag is available on pypi: https://pypi.python.org/pypi/SciStag
* The source is hosted on GitHub: https://github.com/SciStag/SciStag
* The documentation is available on ReadTheDocs: https://scistag.readthedocs.io/

---

This project is still under heavy development and in a very early stage - 
feel free to experiment with the modules and  examples which are already 
provided.

The goal of **SciStag** is to bundle the strengths of the many small, awesome 
Python technologies from OpenCV via Flask to Pandas and enable users to combine 
these libraries and build awesome data driven solutions with a minimum amount of
code.

SciStag currently consists of the following so called **stags**:

## VisLog - (short for VisualLogStag)

* Allows the dynamic creation of documentation in HTML, Markdown and text format
and the fast data evaluation through its built-in in-place reload of Python
modules.

## ImageStag

- Image analysis and modification made easy by combining the strengths of PILLOW, OpenCV and SKImage.

## MediaStag

- Easy integration of streaming media data such as videos into your solution.

## DataStag

- Low-latency inter-container and -process exchange of image and other binary data for Computer Vision and other data
  intensive microservice architectures.

## RemoteStag

- Remote and asynchronous task execution - such as a neural network inference

## WebStag

* Helpful tools for accessing, processing web data and the easy provision
of Python components as local microservices.

## FileStag

* Tools for handling for large amount of files in a data engineering process 
such as easy scanning and handling data in an Azure Storage.

---

## Setup

SciStag comes completely bundled with all required standard components.

`pip install scistag[full]` or when using poetry `poetry add scistag[full]` and you are ready to go! :)

### Optional components

* ImageStag (and other components using ImageStag) support the rendering of HTML and websites via
  [imgkit](https://pypi.org/project/imgkit/). If you do not use any of our pre-built Docker images please follow the
  instructions on https://pypi.org/project/imgkit/ for your operating system if you want to make use of HTML rendering.

## License

Copyright (c) 2022-present Michael Ikemann.

Released under the terms of the **MIT License**.

### Third-party data

The SciStag module on PyPi is bundled with the following data:

* The [Roboto](https://fonts.google.com/specimen/Roboto) font - licensed and distributed under the terms of
  the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
* The [Roboto Flex](https://github.com/googlefonts/roboto-flex) font - licensed under
  the [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web)
* The [JetBrains Mono](https://www.jetbrains.com/lp/mono/) font - licensed under
  the [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web).
* [Iconic font](https://github.com/Templarian/MaterialDesign-Webfont) by the Material Design Icons community covered
  by [SIL Open Font License 1.1](http://scripts.sil.org/cms/scripts/page.php?item_id=OFL_web)
* Emojis and country flags from the [Noto Emoji](https://github.com/googlefonts/noto-emoji) project. Tools and most
  image resources are under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
    * Flag images under the public domain or otherwise exempt from copyright.
* The emoji unicode character name mappings and details are based upon the unicode data files, Copyright © 1991-2022
  Unicode, Inc, licensed under the terms of the [UNICODE, INC. LICENSE AGREEMENT](https://www.unicode.org/license.txt)

### Third-party source code

* Contains portions of code from [imkgit](https://github.com/jarrekk/imgkit), Copyright (C) 2016 Cory Dolphin, Olin
  College, released under the terms of the **MIT License**.

## Contributors

SciStag is developed by Michael Ikemann / [@Alyxion](https://github.com/Alyxion). - Feel free to reach out to me
via [LinkedIn](https://www.linkedin.com/in/michael-ikemann/).

