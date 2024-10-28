# Add Custom Plugins Path

In this projects, several packages are located in `./packages`, which is not a default Python PATH. This means **that path will not be included when Python try searching for packages used in program**.

With Conda, we could manually add the path with `conda-build` and `conda develop` command:

```shell
conda develop ./packages
```

```shell
# output
(compilers) PS C:\Data\Code Repos\Compilers\code\py_impl> conda develop ./packages
path exists, skipping C:\Data\Code Repos\Compilers\code\py_impl\packages
completed operation for: C:\Data\Code Repos\Compilers\code\py_impl\packages
```

You may need to restart your IDE to reflect the changes.