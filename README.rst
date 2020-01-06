Bonelab
=======
Collection of scripts used in the `Bone Imaging Laboratory`_.

|Build Status|_

.. _Bone Imaging Laboratory: https://bonelab.ucalgary.ca/
.. |Build Status| image:: https://dev.azure.com/babesler/Bone%20Imaging%20Laboratory/_apis/build/status/Bonelab.Bonelab?branchName=master
.. _Build Status: https://dev.azure.com/babesler/Bone%20Imaging%20Laboratory/_build/latest?definitionId=12&branchName=master

Install
=======
.. code-block:: bash

    # It is recommended to use anaconda and install from the environment file
    conda env create -f environment.yml

    # ... alternatively, you can setup the environment directly
    conda create -n bl -c numerics88 -c conda-forge python=3.8 n88tools

    # Activate the environemnt
    conda activate bl

    # Install in an 'editable' format 
    pip install -e .

    # ... or you can run the alternative method
    python setup.py install

Installing in an 'editable' format allows one to make changes to the code that
can be immediately used by the binary programs. There is then no need to reinstall
with every edit.

Running Tests
=============
.. code-block:: bash

    # Be at the root
    cd bonelab

    # Run tests
    nosetests tests/

Downloading Bonelab Example Data
================================
A collection of `example data`_ is provided by the `Bone Imaging Laboratory`_.

.. _example data: https://github.com/Bonelab/BonelabData

These data can be fetched by executing the command ``blDownloadData`` in your terminal.
Currently, the data is downloaded into the user's directory under the directory ``~/.bldata``.
Please see ``blDownloadData -h`` for additional information.
