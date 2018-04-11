

    $ pip install file.io-cli

&mdash; *Command-line tool to upload files to https://file.io*

  [file.io]: https://www.file.io

### Synopsis

```
$ file.io --help
usage: file.io [-h] [--version] [-e E] [-n NAME] [-q] [-c] [file]

Upload a file to file.io and print the download link. Supports stdin.

positional arguments:
  file                  the file to upload

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -e E, --expires E     set the expiration time for the uploaded file
  -n NAME, --name NAME  specify or override the filename
  -q, --quiet           hide the progress bar
  -c, --clip            copy the URL to your clipboard
```

### Examples

Upload a TAR file generated on-the-fly:

    $ tar -cf- Biography | file.io --name Biography.tar
    / (4MB)
    https://file.io/QiNG1U

Upload a file from a path and copy the link to the clipboard:

    $ file.io hello.txt --clip
    [===================================================] 100%
    https://file.io/pgiPc2 (copied to clipboard)
    $ curl https://file.io/pgiPc2
    Hello, World!
