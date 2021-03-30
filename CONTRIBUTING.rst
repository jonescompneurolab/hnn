Contributions
-------------

Contributions (including bug reports, fixes, and features additions) are welcome
from the public open source community subject to the terms in the
[Brown University Software License](LICENSE). For any contribution, please first
create an issue describing current behavior and if applicable, the change
proposed. Changes should be submitted in the form of pull requests
that reference the previously created issue.

Once the implementation of a piece of functionality is considered to be bug
free it can be incorporated into the master branch.

All users and contributors to HNN are expected to follow our `code of conduct`_

To help developing HNN, you will need a few adjustments to your
installation as shown below.

Running tests
=============

To run the tests using ``pytest``, you need to have the git cloned ``hnn``
repository with an editable pip install::

    $ git clone https://github.com/jonescompneurolab/hnn --depth 1
    $ cd hnn
    $ python setup.py develop

Then, install the following python packages::

    $ pip install flake8 pytest pytest-cov

The following tests should pass for contributions to be merged::

    $ flake8 --count --exclude  __init__.py
    $ py.test hnn/tests/

Creating releases
=================

After every release creation, assets (``.tar.gz`` and ``.zip`` files) need to be uploaded
to GitHub because those are the files that users will download when following our installation
instructions. This will ideally be replaced by a ``pip``-based installation in the future. For
now, using assets for each release allow download counts to be retrieved using the GitHub API.
Note, that the automatically created assets with each release, named "Source code" do not have
download stats tracked. Also the installation instructions point directly to the uploaded
assets named ``hnn.tar.gz`` and ``hnn.zip``.

Steps to create a new release:

#. `Draft a new release`_ on GitHub with a tag following the scheme: ``v1.3.2``. Include a
    description of significant changes, features, and bug fixes in user-understandable terms.
    Click the "Save draft" button.
#. Download the automatically generated "Source code" files to your system
#. Rename files::

    $ mv v1.3.2.zip hnn.zip
    $ mv v1.3.2.tar.gz hnn.tar.gz

#. Upload files to the newly created release, and "Publish release"

.. _code of conduct: CODE_OF_CONDUCT.md
.. _Draft a new release: https://github.com/jonescompneurolab/hnn/releases/new