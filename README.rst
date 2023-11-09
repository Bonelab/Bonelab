Bonelab
=======
Collection of scripts used in the `Bone Imaging Laboratory`_.

|Build Status|_

.. _Bone Imaging Laboratory: https://bonelab.ucalgary.ca/
.. |Build Status| image:: https://github.com/Bonelab/Bonelab/actions/workflows/pyci.yml/badge.svg
.. _Build Status: https://github.com/Bonelab/Bonelab/actions

Guiding Principles
==================
- **Python**      All source code is Python, no C++, ergo no compilation
- **Examples**    Please do upload individual, one-off project scripts to the /examples directory!
- **Open source** The whole world can see your code, and the whole world can contribute back
- **Testing**     Automatically runs tests on a server. So, please write your tests!

Install
=======

.. code-block:: bash

    # Clone the repository onto your computer and change into the directory.
    # ... with SSH authentication
    git clone git@github.com:Bonelab/Bonelab.git
    # ... or straight HTTPS
    git clone https://github.com/Bonelab/Bonelab.git

    # setup the environment
    conda create -n bl -c numerics88 -c conda-forge python=3 pyqt n88tools simpleitk pbr nose six pydicom gdcm

    # ... or start fresh
    conda create -n bl -c numerics88 -c conda-forge python=3 n88tools pbr nose

    # Activate the environemnt
    conda activate bl
    
    # change directory into the Bonelab repo
    cd Bonelab

    # Install in an 'editable' format
    pip install -e .

Installing in an 'editable' format allows changes to the code to be immediately reflected in your programs.
This removes the need to run ``pip install`` with each change. However, changing entry points in
``setup.cfg`` will require re-runing ``pip install``.


Utilities
=========

bonelab.io
----------

:code:`bonelab.io.download_data`

- environment variables for downloading Bonelab test data

:code:`bonelab.io.sitk_helpers`

- dictionary of file types and casting types for reading and writing 2D raster images with :code:`SimpleITK`


:code:`bonelab.io.vtk_helpers`

- utility functions for reading and writing images with :code:`vtk` and :code:`vtkbone`
- particularly useful functions for properly writing AIMs!

bonelab.util
----

:code:`bonelab.util.aim_calibration_header`

- utility functions for parsing calibration coefficients from AIM calibration headers

:code:`bonelab.util.echo_arguments`

- utility function to use with a command-line application, or a function, to automatically print the arguments to the terminal

:code:`bonelab.util.multiscale_registration`

- utility functions for performing multi-scale Demons registration with SimpleITK

:code:`bonelab.util.n88_util`

- utility functions for extracting fields from n88models as :code:`numpy` arrays for visualization or processing

:code:`bonelab.util.time_stamp`

- utility function for printing a message along with a time stamp, for logging, debugging, etc.

:code:`bonelab.util.vtk_util`

- utility functions for converting data between :code:`vtk.vtkImageData` and :code:`np.ndarray` formats

:code:`bonelab.util.write_csv`

- utility function for writing data stored in a dictionary to a csv file

Command Line Apps
=================

Here is a list of all of the command-line apps that get installed along with the bonelab package.
For detailed usage instructions, type the command followed by :code:`-h` into the terminal
with the :code:`bl` environment activated.

.. list-table::
   :widths: 25 100
   :header-rows: 1

   * - Command
     - Description
   * - :code:`aimod`
     - read in an AIM and examine or modify spacing, origin, and dimensions
   * - :code:`aix`
     - read in an AIM and parse through the processing log
   * - :code:`blDownloadData`
     - download the Bonelab test data
   * - :code:`blExtractFields`
     - extract fields from an n88model and write them to an image
   * - :code:`blImage2ImageSeries`
     - convert a 3D image to a sequence of 2D images
   * - :code:`blImageConvert`
     - convert images between file types
   * - :code:`blImageSeries2Image`
     - convert a sequence of 2D images (including some DICOMs) to a 3D image
   * - :code:`blImageComputeOverlap`
     - compute Dice and Jaccard with two images containing masks (can be multi-class)
   * - :code:`blImageMirror`
     - mirror an image across a plane normal to one of the axes
   * - :code:`blMuscle`
     - segment and quantitatively analyze muscle in calibrated CT
   * - :code:`blPseudoCT`
     - Generate pseudo-CT image from MRI image
   * - :code:`blSliceViewer`
     - interactive 2D slice viewer
   * - :code:`blVisualizeSegmentation`
     - interactive 2D slice viewer with segmentation overlay
   * - :code:`blRapidPrototype`
     - convert STLs to binary images (or vice versa), view STLs, take the intersection or union or two STLs, create STLs of various 3D shapes
   * - :code:`blRegBCn88modelgenerator`
     - this is like n88modelgenerator except the boundary conditions will be modified using a rigid transformation
   * - :code:`blRegBCtransformresults`
     - transform results from a solved FAIM model that was generated by :code:`blRegBCn88modelgenerator`
   * - :code:`scrub_vms_extension`
     - remove version extension that VMS adds to filenames (e.g. TEST.AIM;1 becomes TEST.AIM)
   * - :code:`blBPAQ`
     - analyze BPAQ questionnaire data extracted from REDCap
   * - :code:`blQtViewer`
     - GUI app that can do viewing, point-picking, rigid registration (w/ ICP)
   * - :code:`blQtBasic`
     - GUI app demonstrating the basic integration of :code:`vtk` and :code:`PyQT`
   * - :code:`blAutocontour`
     - (WIP, do not use!) Re-implementation of Helen Buie's IPL autocontour algorithm
   * - :code:`blImageFilter`
     - read an image and extract a sub-volume, apply thresholding, or examine the intensity distribution and run :code:`aix`
   * - :code:`blPanningVideo`
     - read in an image and create a video or gif panning through 2D slices
   * - :code:`blITKSnapAnnotParser`
     - read in an annotation file generated by ITK-Snap and parse out manually measured distances
   * - :code:`blRegistration`
     - perform rigid registration on two images
   * - :code:`blRegistrationDemons`
     - perform deformable registration on two images
   * - :code:`blRegistrationApplyTransform`
     - apply a transformation to an image
   * - :code:`blRegistrationLongitudinal`
     - perform (rigid) longitudinal registration on a time series of images
   * - :code:`blAdaptiveLocalThresholding`
     - segment bone from an AIM using adaptive local thresholding

Running Tests
=============
.. code-block:: bash

    # Be at the root
    cd Bonelab

    # Run tests
    nosetests tests/

Downloading Bonelab Example Data
================================
A collection of `example data`_ is provided by the `Bone Imaging Laboratory`_.

.. _example data: https://github.com/Bonelab/BonelabData

These data can be fetched by executing the command ``blDownloadData`` in your terminal.
Currently, the data is downloaded into the user's directory under the directory ``~/.bldata``.
Please see ``blDownloadData -h`` for additional information.

Adding a New Application
========================
If you're going to contribute to the repository, it is suggested you create a branch:

.. code-block:: bash

    $ git checkout master
    $ git pull
    $ git checkout -b <BRANCH_NAME>

Merge the branch once you're certain your changes won't break other code.

To add a new application, do the following:

- Add entry point in setup.cfg
- Add file with main function in bonelab.cli
- Rerun `pip install -e .`
- Add tests to tests.cli. test_cli_setup.py and, if appropriate, add other tests.

