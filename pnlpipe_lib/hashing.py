"""
(original code from https://github.com/cakepietoast/checksumdir, modified
to add 'included_extensions' option)

Function for deterministically creating a single hash for a directory of files,
taking into account only file contents and not filenames.

"""

import os
import hashlib
import re
from plumbum import local

HASH_FUNCS = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512
}


def dirhash(dirname,
            hashfunc='md5',
            excluded_files=None,
            ignore_hidden=False,
            followlinks=False,
            excluded_extensions=None,
            included_extensions=None):

    if not excluded_files:
        excluded_files = []

    if not excluded_extensions:
        excluded_extensions = []

    if not os.path.isdir(dirname):
        raise TypeError('{} is not a directory.'.format(dirname))

    def include_file(f):
        if ignore_hidden and f.startswith('.') and not re.search(r'/\.', f):
            return False
        return f not in excluded_files \
        and not any([f.endswith(ext) for ext in excluded_extensions]) \
        and (not included_extensions or any(f.endswith(ext) for ext in included_extensions))

    hashvalues = []
    for root, dirs, files in os.walk(
            dirname, topdown=True, followlinks=followlinks):
        if ignore_hidden and re.search(r'/\.', root):
            continue
        hashvalues.extend([filehash(local.path(root) / f, hashfunc)
                           for f in files if include_file(f)])
    return reduce_hash(hashvalues, hashfunc)

def _get_hasher(hashfunc):
    hash_func = HASH_FUNCS.get(hashfunc)
    if not hash_func:
        raise NotImplementedError('{} not implemented.'.format(hashfunc))
    return hash_func()


def filehash(filepath, hashfunc='md5'):
    hasher = _get_hasher(hashfunc)
    blocksize = 64 * 1024
    with open(filepath, 'rb') as fp:
        while True:
            data = fp.read(blocksize)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()


def reduce_hash(hashlist, hashfunc):
    hasher = _get_hasher(hashfunc)
    for hashvalue in sorted(hashlist):
        hasher.update(hashvalue.encode('utf-8'))
    return hasher.hexdigest()
