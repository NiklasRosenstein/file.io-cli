
import setuptools

with open('requirements.txt') as fp:
  install_reqs = fp.readlines()

setuptools.setup(
  name = 'file.io-cli',
  version = '1.0.0',
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  license = 'MIT',
  description = 'Command-line tool to upload files to https://file.io',
  url = 'https://github.com/NiklasRosenstein/file.io-cli',
  install_requires = install_reqs,
  py_modules = ['file_io_cli'],
  entry_points = dict(
    console_scripts = [
      'file.io = file_io_cli:_entry_point'
    ]
  )
)
