# Bonelab

---

Collection of scripts used in the [Bone Imaging Laboratory](https://bonelab.ucalgary.ca/).

Main branch test status: [![Python CI](https://github.com/Bonelab/Bonelab/actions/workflows/pyci.yml/badge.svg)](https://github.com/Bonelab/Bonelab/actions)

---

## Guiding Principles

- **Python** All source code is Python, no C++, ergo no compilation
- **Examples** Please do upload individual, one-off project scripts to the /examples directory!
- **Open source** The whole world can see your code, and the whole world can contribute back
- **Testing** Automatically runs tests on a server. So, please write your tests!

---

## Install

```commandline
# Clone the repository onto your computer and change into the directory.
# ... with SSH authentication
git clone git@github.com:Bonelab/Bonelab.git
# ... or straight HTTPS
git clone https://github.com/Bonelab/Bonelab.git

# setup the environment
conda create -n bl -c numerics88 -c conda-forge python=3 n88tools pbr nose

# Activate the environemnt
conda activate bl

# change directory into the Bonelab repo
cd Bonelab

# Install in an 'editable' format
pip install -e .
```

Install for M1 MACs ([instructions from here](https://blog.rtwilson.com/how-to-create-an-x64-intel-conda-environment-on-your-apple-silicon-mac-arm-conda-install/))

```commandline
# Clone the repository onto your computer and change into the directory.
# ... with SSH authentication
git clone git@github.com:Bonelab/Bonelab.git
# ... or straight HTTPS
git clone https://github.com/Bonelab/Bonelab.git

# setup the environment
CONDA_SUBDIR=osx-64 conda create -n bl -c numerics88 -c conda-forge python=3 n88tools pbr nose PyQt

# Activate the environemnt
conda activate bl

# Tell conda to always not use the ARM directory for this env
conda env config vars set CONDA_SUBDIR=osx-64

# Deactivate and reactivate
conda deactivate
conda activate bl

# change directory into the Bonelab repo
cd Bonelab

# Install in an 'editable' format
pip install -e .
```

Installing in an 'editable' format allows changes to the code to be immediately reflected in your programs.
This removes the need to run `pip install` with each change. However, changing entry points in
`setup.cfg` will require re-running `pip install`.

---

## Utilities

### `bonelab.io`

`bonelab.io.download_data`

- environment variables for downloading Bonelab test data

`bonelab.io.sitk_helpers`

- dictionary of file types and casting types for reading and writing 2D raster images with :code:`SimpleITK`

`bonelab.io.vtk_helpers`

- utility functions for reading and writing images with `vtk` and `vtkbone`
- particularly useful functions for properly writing AIMs!

### `bonelab.util`

`bonelab.util.aim_calibration_header`

- utility functions for parsing calibration coefficients from AIM calibration headers

`bonelab.util.echo_arguments`

- utility function to use with a command-line application, or a function, to automatically print the arguments to the terminal

`bonelab.util.multiscale_registration`

- utility functions for performing multi-scale Demons registration with SimpleITK

`bonelab.util.n88_util`

- utility functions for extracting fields from n88models as :code:`numpy` arrays for visualization or processing

`bonelab.util.time_stamp`

- utility function for printing a message along with a time stamp, for logging, debugging, etc.

`bonelab.util.vtk_util`

- utility functions for converting data between `vtk.vtkImageData` and `np.ndarray` formats

`bonelab.util.write_csv`

- utility function for writing data stored in a dictionary to a csv file

---

## Command Line Apps

Here is a list of all of the command-line apps that get installed along with the bonelab package.
For detailed usage instructions, type the command followed by `-h` into the terminal
with the `bl` environment activated.

| Command                        | Description                                                                                                                                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `aimod`                        | read in an AIM and examine or modify spacing, origin, and dimensions                                                                                                                                               |
| `aix`                          | read in an AIM and parse through the processing log                                                                                                                                                                |
| `blDownloadData`               | download the Bonelab test data                                                                                                                                                                                     |
| `blExtractFields`              | extract fields from an n88model and write them to an image                                                                                                                                                         |
| `blImage2ImageSeries`          | convert a 3D image to a sequence of 2D images                                                                                                                                                                      |
| `blImageConvert`               | convert images between file types                                                                                                                                                                                  |
| `blImageSeries2Image`          | convert a sequence of 2D images (including some DICOMs) to a 3D image                                                                                                                                              |
| `blImageComputeOverlap`        | compute Dice and Jaccard with two images containing masks (can be multi-class)                                                                                                                                     |
| `blImageMirror`                | mirror an image across a plane normal to one of the axes                                                                                                                                                           |
| `blMuscle`                     | segment and quantitatively analyze muscle in calibrated CT                                                                                                                                                         |
| `blPseudoCT`                   | Generate pseudo-CT image from MRI image                                                                                                                                                                            |
| `blSliceViewer`                | interactive 2D slice viewer                                                                                                                                                                                        |
| `blVisualizeSegmentation`      | interactive 2D slice viewer with segmentation overlay                                                                                                                                                              |
| `blRapidPrototype`             | convert STLs to binary images (or vice versa), view STLs, take the intersection or union or two STLs, create STLs of various 3D shapes                                                                             |
| `blRegBCn88modelgenerator`     | this is like n88modelgenerator except the boundary conditions will be modified using a rigid transformation                                                                                                        |
| `blRegBCtransformresults`      | transform results from a solved FAIM model that was generated by `blRegBCn88modelgenerator`                                                                                                                        |
| `scrub_vms_extension`          | remove version extension that VMS adds to filenames (e.g. TEST.AIM;1 becomes TEST.AIM)                                                                                                                             |
| `blBPAQ`                       | analyze BPAQ questionnaire data extracted from REDCap                                                                                                                                                              |
| `blQtViewer`                   | GUI app that can do viewing, point-picking, rigid registration (w/ ICP)                                                                                                                                            |
| `blQtBasic`                    | GUI app demonstrating the basic integration of `vtk` and `PyQT`                                                                                                                                                    |
| `blAutocontour`                | (WIP, do not use!) Re-implementation of Helen Buie's IPL autocontour algorithm                                                                                                                                     |
| `blImageFilter`                | read an image and extract a sub-volume, apply thresholding, or examine the intensity distribution and run `aix`                                                                                                    |
| `blPanningVideo`               | read in an image and create a video or gif panning through 2D slices                                                                                                                                               |
| `blITKSnapAnnotParser`         | read in an annotation file generated by ITK-Snap and parse out manually measured distances                                                                                                                         |
| `blRegistration`               | perform rigid registration on two images                                                                                                                                                                           |
| `blRegistrationDemons`         | perform deformable registration on two images                                                                                                                                                                      |
| `blRegistrationApplyTransform` | apply a transformation to an image                                                                                                                                                                                 |
| `blRegistrationLongitudinal`   | perform (rigid) longitudinal registration on a time series of images                                                                                                                                               |
| `blAdaptiveLocalThresholding`  | segment bone from an AIM using adaptive local thresholding                                                                                                                                                         |
| `blFFTLaplaceHamming`          | segment bone from an AIM using FFT Laplace Hamming filtering                                                                                                                                                       |
| `blTreeceThickness`            | compute cortical thickness from an image and bone segmentation using the Treece method                                                                                                                             |
| `blAIMs2NIIs`                  | Convert an AIM, and optionally it's associated masks, to nifti image(s). The image and it's masks will be padded so they align.                                                                                    |
| `blMask2AIM `                  | Convert a binary mask in nifti format back to AIM format, using a reference AIM as a base so the AIM you create will line up properly with the associated image when you go back to the VMS.                       |
| `blMasks2AIMs`                 | Same as `blMask2AIM`, except instead of a binary mask nifti you give a multiclass mask nifti and you provide a set of class values and associated mask labels to append to the filename when creating binary AIMs. |
| `blMaskFilter `                  | Read a mask and apply erosion, dilation, opening, or closing.                       |
---

## Running Tests

```commandline
# Be at the root
cd Bonelab

# Run tests
nosetests tests/
```

---

## Downloading Bonelab Example Data

A collection of [example data](https://github.com/Bonelab/BonelabData)
is provided by the [Bone Imaging Laboratory](https://bonelab.ucalgary.ca/).

These data can be fetched by executing the command `blDownloadData` in your terminal.
Currently, the data is downloaded into the user's directory under the directory `~/.bldata`.
Please see `blDownloadData -h` for additional information.

---

## Adding a New Application

Contributions or changes to the repository should be made using the trunk and branch
development style. You first create a branch:

```commandline
git checkout master
git pull
git checkout -b <your-name>/<branch-name>
```

As you develop locally, periodically run the tests to ensure your changes haven't broken anything:

```commandline
nosetests tests/
```

Once you are satisfied with your changes, use the web interface to submit a pull request.
Get someone more senior (/ Steve) to review your changes, and merge once review is done.

To add a new command-line application, do the following:

- Add file with main function in `bonelab.cli`
- Add entry point to `setup.cfg` that points to the new file
- Rerun `pip install -e .`
- Add tests to `tests.cli`, `test_cli_setup.py` and, if appropriate, add other tests.

If you're going to add something, please do add at least unit tests so that as other people
edit the repository we can be sure they don't break your code.

Also make sure you document your new cool stuff in the README (this file) so that
other people in the lab know about it!
