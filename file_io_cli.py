# Copyright (c) 2018 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from __future__ import division, print_function

import argparse
import clipboard
import json
import os
import requests
import subprocess
import sys
import threading
import time
import uuid

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '1.0.1'


class MultipartFileEncoder(object):

  def __init__(self, field, fp, filename=None, boundary=None, headers=None):
    self.field = field
    self.fp = fp
    self.filename = filename
    self.boundary = (boundary or uuid.uuid4().hex).encode('ascii')
    self.content_type = b'multipart/form-data; boundary=' + self.boundary

    headers = dict(headers or {})

    if 'Content-Disposition' not in headers:
      disposition = 'form-data; name="{}"'.format(self.field)
      if self.filename:
        disposition += '; filename="{}"'.format(self.filename)
      headers['Content-Disposition'] = disposition

    if 'Content-Type' not in headers:
      headers['Content-Type'] = 'application/octet-stream'

    self.headers = b'\r\n'.join('{}: {}'.format(k, v).encode('ascii') for k, v in headers.items())

  def compute_size(self, include_final_boundary=True):
    pos = self.fp.tell()
    self.fp.seek(0, os.SEEK_END)
    size = self.fp.tell()
    self.fp.seek(pos)
    size += len(self.boundary) + 4 + 4 + len(self.headers) + 2
    if include_final_boundary:
      size += 6 + len(self.boundary)
    return size

  def iter_encode(self, include_final_boundary=True, chunksize=8096):
    yield b'--'
    yield self.boundary
    yield b'\r\n'

    yield self.headers
    yield b'\r\n'
    yield b'\r\n'

    # TODO: Check if boundary value occurs in data body.
    while True:
      data = self.fp.read(chunksize)
      if not data: break
      yield data

    yield b'\r\n'

    if include_final_boundary:
      yield b'--'
      yield self.boundary
      yield b'--\r\n'


class GeneratorFileReader(object):

  def __init__(self, gen):
    self.gen = gen
    self.buffer = b''

  def readable(self):
    return True

  def read(self, n=None):
    if n is None:
      res = self.buffer + b''.join(self.gen)
      self.buffer = b''
      return res
    elif n <= 0:
      return b''
    else:
      res = b''
      while n > 0:
        part = self.buffer[:n]
        res += part
        self.buffer = self.buffer[n:]
        n -= len(part); assert n >= 0
        if not self.buffer:
          try:
            self.buffer = next(self.gen)
          except StopIteration:
            break
        else:
          break
      return res


class FileMonitor(object):

  def __init__(self, fp, callback=None):
    self.fp = fp
    self.bytes_read = 0
    self.callback = callback

  def __getattr__(self, key):
    return getattr(self.fp, key)

  def read(self, n):
    res = self.fp.read(n)
    self.bytes_read += len(res)
    if self.callback:
      self.callback(self)
    return res


class ProgressDisplay(object):

  SPINCHARS = '\\|/-'

  def __init__(self, n_max=None):
    self.n_max = n_max
    self.alteration = 0
    self.last_print = None

  def update(self, n_read, force=False):
    if not force and self.last_print is not None and time.clock() - self.last_print < 0.25:
      return
    self.last_print = time.clock()
    self.__clear_line(file=sys.stderr)
    if self.n_max is None:
      c = self.SPINCHARS[self.alteration%len(self.SPINCHARS)]
      print('\r{} ({})'.format(c, self.human_size(n_read)),
        end='', file=sys.stderr)
    else:
      w = 60
      p = n_read / self.n_max
      l = int(w * p)

      bar = '[' + '=' * l + ' ' * (w-l) + ']'
      print('\r{} {}% ({} / {})'.format(bar, int(p*100),
        self.human_size(n_read), self.human_size(self.n_max)),
        end='', file=sys.stderr)
    sys.stderr.flush()
    self.alteration += 1

  def finish(self):
    print(file=sys.stderr)

  @staticmethod
  def __clear_line(file=None):
    print('\r\33[K', end='', file=file)


  @staticmethod
  def human_size(n_bytes, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    # https://stackoverflow.com/a/43750422/791713
    return str(n_bytes) + units[0] if n_bytes < 1024 else ProgressDisplay.human_size(n_bytes>>10, units[1:])


def stream_file(fp, chunksize=8192):
  while True:
    data = fp.read(chunksize)
    if data: yield data
    else: break


def spawn_process(*args, **kwargs):
  on_exit = kwargs.pop('on_exit', None)
  def worker():
    subprocess.call(*args, **kwargs)
    if on_exit is not None:
      on_exit()
  threading.Thread(target=worker).start()


def main(prog=None, argv=None):
  parser = argparse.ArgumentParser(prog=prog, description='Upload a file to file.io and print the download link. Supports stdin.')
  parser.add_argument('--version', action='version', version=__version__)
  parser.add_argument('-e', '--expires', metavar='E',help='set the expiration time for the uploaded file')
  parser.add_argument('-n', '--name', help='specify or override the filename')
  parser.add_argument('-q', '--quiet', action='store_true', help='hide the progress bar')
  parser.add_argument('-c', '--clip', action='store_true', help='copy the URL to your clipboard')
  parser.add_argument('-t', '--tar', metavar='PATH', help='create a TAR archive from the specified file or directory')
  parser.add_argument('-z', '--gzip', action='store_true', help='filter the TAR archive through gzip (only with -t, --tar)')
  parser.add_argument('file', nargs='?', help='the file to upload')
  args = parser.parse_args()

  if not args.file and not args.tar and sys.stdin.isatty():
    parser.print_usage()
    return 0
  if args.file and args.tar:
    parser.error('conflicting options: file and -t, --tar')

  if not args.name and args.file:
    args.name = os.path.basename(args.file)
  elif not args.name and args.tar:
    args.name = os.path.basename(args.tar) + ('.tgz' if args.gzip else '.tar')

  if args.tar:
    r, w = os.pipe()
    flags = '-czf-' if args.gzip else '-cf-'
    spawn_process(['tar', flags, args.tar], stdout=w, on_exit=lambda: os.close(w))
    file_size = None
    fp = os.fdopen(r, 'rb')
  elif args.file:
    file_size = os.stat(args.file).st_size
    fp = open(args.file, 'rb')
  else:
    file_size = None
    fp = sys.stdin if sys.version_info[0] == 2 else sys.stdin.buffer

  if not args.quiet:
    progress = ProgressDisplay(file_size)
    fp = FileMonitor(fp, lambda f: progress.update(f.bytes_read))

  encoder = MultipartFileEncoder('file', fp, filename=args.name or 'file')
  stream = GeneratorFileReader(encoder.iter_encode())

  headers = {'Content-Type': encoder.content_type}
  params = {}
  if args.expires:
    params['expires'] = args.expiry

  url = 'http://file.io'
  if params:
    url += '?' + urlencode(params)

  try:
    response = requests.post(url, params=params,
      data=stream_file(stream), headers=headers)
    response.raise_for_status()
  except BaseException as exc:
    if not args.quiet:
      progress.finish()
    if isinstance(exc, KeyboardInterrupt):
      print('aborted.', file=sys.stderr)
      return 1
    raise
  else:
    if not args.quiet:
      progress.update(fp.bytes_read, force=True)
      progress.finish()

  link = response.json()['link']

  if args.clip:
    print(link, '(copied to clipboard)')
    clipboard.copy(link)
  else:
    print(link)


_entry_point = lambda: sys.exit(main())

if __name__ == '__main__':
  _entry_point()
