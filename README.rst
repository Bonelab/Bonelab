Bonelab
=======
Collection of scripts used in the `Bone Imaging Laboratory`.

.. _Bone Imaging Laboratory: https://bonelab.ucalgary.ca/

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
with ever edit.

Running Tests
=============
.. code-block:: bash

    # Be at the root
    cd bonelab

    # Run tests
    nosetests tests/
