# file.io-cli

    $ pip install file.io-cli

Command-line tool to upload files to https://file.io

  [file.io]: https://www.file.io

### Synopsis

```
$ file.io --help
usage: file.io [-h] [--version] [-e E] [-n NAME] [-q] [-c] [-t PATH] [-z] [file]

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
  -t PATH, --tar PATH   create a TAR archive from the specified file or directory
  -z, --gzip            filter the TAR archive through gzip (only with -t, --tar)
```

### Examples

Upload a file and copy the link:

```
$ file.io hello.txt -c
[============================================================] 100% (15 bytes / 15 bytes)
https://file.io/pgiPc2 (copied to clipboard)
$ cat https://file.io/pgiPc2
Hello, File.io!
```

Upload a compressed archiveCompress a file/directory and upload it (streaming):

```
$ file.io -zt AllMyFiles/
/ (55MB)
https://file.io/sf2La
```

Upload from stdin:

```
$ find .. -iname \*.py | file.io -n file-list.txt
/ (312KB)
https://file.io/uRglUT
```

### Changelog

#### v1.0.3

* Fix declared dependencies in setup script

#### v1.0.2

* Replaced `time.clock` (removed in python 3.8) with `time.perf_counter`
* Minimum Python version is 3.3

#### v1.0.1

* Add `-t, --tar` and `-z, --gzip` options
* Fix NameError when using `-c, --clip`
* Fix progress bar left incomplete

#### v1.0.0

* Initial version
