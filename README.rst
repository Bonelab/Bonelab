Bonelab
=======
Collection of scripts used in the `Bone Imaging Laboratory`_.

|Build Status|_

.. _Bone Imaging Laboratory: https://bonelab.ucalgary.ca/
.. |Build Status| image:: https://dev.azure.com/babesler/Bone%20Imaging%20Laboratory/_apis/build/status/Bonelab.Bonelab?branchName=master
.. _Build Status: https://dev.azure.com/babesler/Bone%20Imaging%20Laboratory/_build/latest?definitionId=12&branchName=master

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
    git clone git@github.com:Bonelab/Bonelab.git

    # It is recommended to use anaconda and install from the environment file
    conda env create -f environment.yml

    # ... alternatively, you can setup the environment directly
    conda create -n bl -c numerics88 -c simpleitk -c conda-forge python=3.7 n88tools pbr nose six simpleitk

    # Activate the environemnt
    conda activate bl

    # Install in an 'editable' format
    pip install -e .

Installing in an 'editable' format allows changes to the code to be immediately reflected in your programs.
This removes the need to run ``pip install`` with each change. However, changing entry points in
``setup.cfg`` will require re-runing ``pip install``.

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

