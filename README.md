# 3DONT viewer

View, query and manually annotate pointclouds ontologies.

### TODO
- [x] select query box
- [x] natural language query box
- [x] scalar query box
- [x] click to view properties of a point
- [x] tree view for details
- [ ] manual annotation tool
- [ ] check if points are selected right
- [ ] scalar field query
- [ ] right click: select all subjects
- [ ] right click: plot feature
- [ ] configure page (namespace)

## License

Unless otherwise noted in `LICENSE` files for specific files or directories,
the [LICENSE](LICENSE) in the root applies to all content in this repository.

## Install

You have to build the wheel from source.

```bash
python -m build --no-isolation --wheel
pip install .
```

## Build

We provide CMake scripts for automating most of the build process, but ask the
user to manually prepare [dependencies](#requirements) and record their paths
in the following CMake cache variables.

* `Numpy_INCLUDE_DIR`
* `PYTHON_INCLUDE_DIR`
* `PYTHON_LIBRARY`
* `Eigen_INCLUDE_DIR`
* `Qt5_DIR`

To set these variables, either use one of CMake's GUIs (ccmake or cmake-gui),
or provide an initial CMakeCache.txt in the target build folder
(for examples of initial cache files, see the CMakeCache.<platform>.txt files)

##### Requirements

Listed are versions of libraries used to develop pptk, though earlier versions
of these libraries may also work.

* [QT](https://www.qt.io/) 5.4
* [Eigen](http://eigen.tuxfamily.org) 3.2.9
* [Python](https://www.python.org/) 2.7+ or 3.6+
* [Numpy](http://www.numpy.org/) 1.13

##### Windows

1. Create an empty build folder

```
>> mkdir <build_folder>
```

2. Create an initial CMakeCache.txt under <build_folder> and use it to provide
values for the CMake cache variables listed above. (e.g. see CMakeCache.win.txt)

3. Type the following...

```
>> cd <build_folder>
>> cmake -G "NMake Makefiles" <source_folder>
>> nmake
>> python setup.py bdist_wheel
>> pip install dist\<.whl file>
```

##### Linux

Similar to building on Windows.

##### Mac

Similar to building on Windows.
