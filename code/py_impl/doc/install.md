# Installation Guide

To fully configure this project and make it runable in your environments, you should do the following step.

## Install Conda

You need to install `conda` as the Python environment manager on your machine. You could follow the official doc below:

https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

## Create Environment

The environment file is located in the root directory of this project: `./environment.yml`, you could run the following command to create a environment based on that file:

```shell
conda env create -f environment.yml
```

Then you can switch to the newly created environment by using following command:

```shell
conda activate compilers
```

## Adding Packages Path

After creating the environments, we also need to mark `./packages` as a path for Python, which allow Python to search for packages in that folder:

```
conda develop ./packages
```

---

After all steps above, you should be able to run the program in the created environment:

```shell
(compilers) YourCLI> python main.py
```

