# 3DONT viewer

View, query and manually annotate pointclouds ontologies.

### TODO
- [x] select query box
- [x] natural language query box
- [x] scalar query box
- [x] click to view properties of a point
- [x] tree view for details
- [x] check if points are selected right
- [x] manual annotation tool
- [x] scalar field query
- [x] right click: select all subjects with this predicate and object
- [x] right click: plot predicate (scalar)
- [x] append OFFSET and LIMIT instead of using template
- [x] error box in gui
- [x] error handling for: wrong output format, empty output, syntax error, connection error...
- [x] highlight subject in treeview
- [x] non visual queries (tabular result box?)
- [x] highlight subject name
- [x] legend scalar
- [x] adjust licensing
- [x] persistent configuration (platformdirs)
- [ ] scalar templates
- [ ] nl queries
- [ ] refactor input dialogs
- [ ] import pointclouds etc.
- [ ] add default to scalar queries equal to color
- [ ] configure page (namespace)
- [ ] fix viewer focus issue
- [ ] better loading screen
- [ ] gui error report (generic)
- [ ] override config with cli arguments
 
## License

The LICENSE_PPTK file is the license of the viewer used as a base for this project. It is relative to the content of the folder
`threedont/gui/viewer` and the file `threedont/app/viewer.py`.

## Install

You have to build the wheel from source.

```bash
python -m build --no-isolation --wheel
pip install .
```

## Build

We provide CMake scripts for automating most of the build process, just 
follow the standard cmake workflow to build:

```bash
mkdir build
cd build
cmake ..
make -j4
```

##### Requirements

Listed are versions of libraries used to develop 3dont, though earlier versions
of these libraries may also work.

* [QT](https://www.qt.io/) 6.9
* [Eigen](http://eigen.tuxfamily.org) 3.2.9
* [Python](https://www.python.org/) 3.6+
* [Numpy](http://www.numpy.org/) 1.13

## Build with nix

This project has nix support (with flakes). Install nix and enable flakes,
the run `nix build` from the root to build the project. 
You can also use `nix run` and `nix run github:SamueleFacenda/3dont` to run the project 
without downloading the repo.

