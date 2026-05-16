Environment Setup
===========================

Invoke
---------------------------
To make repetitve tasks easier, pyadi-iio utilizes pyinvoke. To see the available options (once pyinvoke is installed) run:

.. code-block:: console

        invoke --list
        Available tasks:

          build           Build python package
          builddoc        Build sphinx doc
          changelog       Print changelog from last release
          checkparts      Check for missing parts in supported_parts.md
          createrelease   Create GitHub release
          libiiopath      Search for libiio python bindings
          precommit       Run precommit checks
          setup           Install required python packages for development through pip
          test            Run pytest tests



Precommit
---------------------------
**pre-commit** is heavily relied on for keeping code in order and for eliminating certain bugs. Be sure to run these checks before submitting code. This can be run through pyinvoke or directly from the repo root as:

.. code-block:: console

        invoke precommit

.. code-block:: console

        pre-commit run --all-files

Set Up Isolated Environment
---------------------------

This section will discuss a method to do isolated development with the correct package versions. The main purpose here is to eliminate any discrepancies that can arise (especially with the linting tools) when running precommit and other checks. This is also useful to not pollute your local global packages. The approach here relies upon leveraging **pyenv** and **pipenv** together.


Install pyenv
^^^^^^^^^^^^^^^^^

**pyenv** is a handy tool for installing different and isolated versions of python on your system. Since distributions can ship with rather random versions of python, pyenv can help us install exactly the versions we want. The quick way to install pyenv is with their bash script:


.. code-block:: bash

 curl https://pyenv.run | bash


Add to your path and shell startup script (.bashrc, .zshrc, ...)

.. code-block:: bash

 export PATH="/home/<username>/.pyenv/bin:$PATH
 eval "$(pyenv init -)"
 eval "$(pyenv virtualenv-init -)"


Install the desired python version

.. code-block:: bash

  pyenv install 3.6.9


Create isolated install with pipenv
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the repo, set python version, and setup env

.. code-block:: bash

  pip3 install -U pipenv
  pyenv local 3.6.9
  git clone git@github.com:analogdevicesinc/pyadi-iio.git
  pipenv install
  pipenv shell
  pipenv install -r requirements.txt
  pipenv install -r requirements_dev.txt


Now at this point we have all the necessary development packages to start working. If you close the current shell you will lose the environment. To return to it, go to the project folder and run:

.. code-block:: bash

  cd <project folder>
  pyenv local 3.6.9
  pipenv shell
