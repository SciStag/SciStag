# Release checklist

* Update the package's version in pyproject.md
  * Lock the poetry file afterwards
* Update the version in scistag/\_\_init__.py
* Move the the project's root directory
* Execute `poetry build`
* Move to tools/test_wheel
    * Update the version number in it's **pyproject.toml**
    * Lock the file
    * Execute `./test_wheel.sh`
* Execute `poetry publish`