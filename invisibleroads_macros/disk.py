import codecs
import fnmatch
import os
import re
import tarfile
import tempfile
import zipfile
from contextlib import contextmanager
from os import chdir, close, getcwd, listdir, makedirs, remove, walk
from os.path import (
    abspath, basename, dirname, exists, expanduser, isdir, islink, join,
    realpath, relpath, sep)
from shutil import copy2, copyfileobj, move, rmtree
from tempfile import _RandomNameSequence, mkdtemp, mkstemp

from .exceptions import BadArchive
from .security import make_random_string, ALPHABET
from .text import unicode_safely


BAD_RELATIVE_PATH = 'relative path must be inside folder'
COMMAND_LINE_HOME = '%UserProfile%' if os.name == 'nt' else '~'
HOME_FOLDER = expanduser('~')
_MINIMUM_UNIQUE_LENGTH = 10


class TemporaryFolder(object):

    def __init__(self, parent_folder=None, suffix='', prefix='tmp'):
        self.folder = make_unique_folder(parent_folder, suffix, prefix)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        super(TemporaryFolder, self).__exit__(
            exception_type, exception_value, exception_traceback)
        remove_safely(self.folder)


class TemporaryPath(object):

    def __init__(self, parent_folder=None, suffix='', prefix='tmp'):
        self.path = make_unique_path(parent_folder, suffix, prefix)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        super(TemporaryPath, self).__exit__(
            exception_type, exception_value, exception_traceback)
        remove_safely(self.path)


class _CustomRandomNameSequence(_RandomNameSequence):

    def next(self):
        return self.__next__()

    def __next__(self):
        choose = self.rng.choice
        return ''.join(choose(ALPHABET) for x in range(_MINIMUM_UNIQUE_LENGTH))


def make_folder(folder):
    'Make sure a folder exists without raising an exception'
    try:
        makedirs(folder)
    except OSError:
        pass
    return folder


def make_unique_folder(
        parent_folder=None, suffix='', prefix='',
        length=_MINIMUM_UNIQUE_LENGTH):
    if parent_folder:
        make_folder(parent_folder)
    suffix = _prepare_suffix(suffix, length)
    return mkdtemp(suffix, prefix, parent_folder)


def make_unique_path(
        parent_folder=None, suffix='', prefix='',
        length=_MINIMUM_UNIQUE_LENGTH):
    if parent_folder:
        make_folder(parent_folder)
    suffix = _prepare_suffix(suffix, length)
    descriptor, path = mkstemp(suffix, prefix, parent_folder)
    close(descriptor)
    return path


def clean_folder(folder):
    'Remove folder contents but keep folder'
    for x_name in listdir(folder):
        x_path = join(folder, x_name)
        remove_safely(x_path)
    return folder


def copy_folder(target_folder, source_folder):
    'Copy contents without removing target_folder'
    from os import readlink, symlink
    if exists(target_folder):
        clean_folder(target_folder)
    else:
        make_folder(target_folder)
    for old_name in listdir(source_folder):
        old_path = join(source_folder, old_name)
        new_path = join(target_folder, old_name)
        if islink(old_path):
            symlink(readlink(old_path), new_path)
        elif isdir(old_path):
            copy_folder(new_path, old_path)
        else:
            copy2(old_path, target_folder)
    return target_folder


def move_folder(target_folder, source_folder):
    'Move contents without removing target_folder'
    if not exists(target_folder):
        move(source_folder, target_folder)
        return target_folder
    clean_folder(target_folder)
    for x_name in listdir(source_folder):
        x_path = join(source_folder, x_name)
        move(x_path, target_folder)
    remove_safely(source_folder)
    return target_folder


def remove_safely(path):
    'Make sure a file or folder does not exist without raising an exception'
    try:
        rmtree(path)
    except OSError:
        try:
            remove(path)
        except OSError:
            pass
    return path


def find_path(folder, file_name):
    'Locate file in folder'
    for root_folder, folder_names, file_names in walk(folder):
        if file_name in file_names:
            file_path = join(root_folder, file_name)
            break
    else:
        raise IOError('cannot find {0} in {1}'.format(file_name, folder))
    return file_path


def find_paths(folder, include_expression='*', exclude_expression=''):
    'Locate files in folder matching expression'
    return [
        unicode_safely(join(root_folder, file_name))
        for root_folder, folder_names, file_names in walk(folder)
        for file_name in fnmatch.filter(file_names, include_expression)
        if not fnmatch.fnmatch(file_name, exclude_expression)]


def resolve_relative_path(relative_path, folder):
    relative_path = relpath(join(folder, expanduser(relative_path)), folder)
    if relative_path.startswith('.'):
        raise IOError(BAD_RELATIVE_PATH)
    return join(folder, relative_path)


def compress(source_folder, target_path=None, excludes=None):
    'Compress folder; specify archive extension (.tar.gz .zip) in target_path'
    if not target_path:
        target_path = source_folder + '.tar.gz'
    if target_path.endswith('.tar.gz'):
        compress_tar_gz(source_folder, target_path, excludes)
    else:
        compress_zip(source_folder, target_path, excludes)
    return target_path


def compress_tar_gz(source_folder, target_path=None, excludes=None):
    'Compress folder as tar archive'
    if not target_path:
        target_path = source_folder + '.tar.gz'
    source_folder = realpath(source_folder)
    with tarfile.open(target_path, 'w:gz', dereference=True) as target_file:
        _process_folder(source_folder, excludes, target_file.add)
    return target_path


def compress_zip(source_folder, target_path=None, excludes=None):
    'Compress folder as zip archive'
    if not target_path:
        target_path = source_folder + '.zip'
    source_folder = realpath(source_folder)
    with zipfile.ZipFile(
        target_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True,
    ) as target_file:
        _process_folder(source_folder, excludes, target_file.write)
    return target_path


def uncompress(source_path, target_folder=None):
    if source_path.endswith('.tar.gz'):
        try:
            source_file = tarfile.open(source_path, 'r:gz')
        except tarfile.ReadError:
            raise BadArchive(
                'could not open archive (source_path=%s)' % source_path)
        default_target_folder = re.sub(r'\.tar.gz$', '', source_path)
    else:
        try:
            source_file = zipfile.ZipFile(source_path, 'r')
        except zipfile.BadZipfile:
            raise BadArchive(
                'could not open archive (source_path=%s)' % source_path)
        default_target_folder = re.sub(r'\.zip$', '', source_path)
    target_folder = target_folder or default_target_folder
    source_file.extractall(target_folder)
    source_file.close()
    return target_folder


def are_same_path(path1, path2):
    return realpath(expand_path(path1)) == realpath(expand_path(path2))


def is_x_parent_of_y(folder, path):
    return realpath(path).startswith(realpath(folder))


def has_name_match(path, expressions):
    name = basename(str(path))
    for expression in expressions or []:
        if fnmatch.fnmatch(name, expression):
            return True
    return False


@contextmanager
def cd(target_folder):
    source_folder = getcwd()
    try:
        chdir(target_folder)
        yield
    finally:
        chdir(source_folder)


def make_enumerated_folder_for(script_path, first_index=1):
    package_name = get_file_basename(script_path)
    if 'run' == package_name:
        package_folder = get_package_folder(script_path)
        package_name = get_file_basename(package_folder)
    return make_enumerated_folder(join(sep, 'tmp', package_name), first_index)


def make_enumerated_folder(base_folder, first_index=1):
    'Make a unique enumerated folder in base_folder'

    def suggest_folder(index):
        return join(base_folder, str(index))

    target_index = first_index
    target_folder = suggest_folder(target_index)
    while True:
        try:
            makedirs(target_folder)
            break
        except OSError:
            target_index += 1
            target_folder = suggest_folder(target_index)
    return target_folder


def get_package_folder(script_path):
    return dirname((script_path))


def change_owner_and_group_recursively(target_folder, target_username):
    'Change uid and gid of folder and its contents, treating links as files'
    from os import lchown     # Undefined in Windows
    from pwd import getpwnam  # Undefined in Windows
    pw_record = getpwnam(target_username)
    target_uid = pw_record.pw_uid
    target_gid = pw_record.pw_gid
    for root_folder, folders, names in walk(target_folder):
        for folder in folders:
            lchown(join(root_folder, folder), target_uid, target_gid)
        for name in names:
            lchown(join(root_folder, name), target_uid, target_gid)
    lchown(target_folder, target_uid, target_gid)


def replace_file_extension(path, extension):
    parent_folder = dirname(path)
    file_basename, file_extension = basename(path).split('.', 1)
    return join(parent_folder, file_basename + extension)


def get_file_basename(path):
    'Return file name without extension (x/y/z/file.txt.zip -> file)'
    return basename(path).split('.', 1)[0]


def get_file_extension(path, max_length=16):
    # Extract extension
    try:
        file_extension = basename(path).split('.', 1)[1]
    except IndexError:
        return ''
    # Sanitize characters
    file_extension = ''.join(x for x in file_extension if x.isalnum() or x in [
        '.', '-', '_',
    ]).rstrip()
    # Limit length
    return '.' + file_extension[-max_length:]


def load_text(source_path):
    return codecs.open(source_path, 'r', encoding='utf-8').read()


def copy_text(target_path, source_text):
    _prepare_path(target_path)
    codecs.open(target_path, 'w', encoding='utf-8').write(source_text)
    return target_path


def copy_file(target_path, source_file):
    _prepare_path(target_path)
    copyfileobj(source_file, open(target_path, 'wb'))
    return target_path


def copy_path(target_path, source_path):
    _prepare_path(target_path)
    copy2(source_path, target_path)
    return target_path


def link_path(target_path, source_path):
    target_path = expanduser(target_path)
    source_path = expanduser(source_path)
    if not exists(source_path):
        raise IOError
    if are_same_path(target_path, source_path):
        return target_path
    if is_x_parent_of_y(target_path, source_path):
        raise ValueError
    try:
        from os import symlink  # Undefined in Windows
    except ImportError:
        return copy_path(target_path, source_path)
    _prepare_path(target_path)
    symlink(source_path, target_path)
    return target_path


def move_path(target_path, source_path):
    _prepare_path(target_path)
    move(source_path, target_path)
    return target_path


def expand_path(path):
    return abspath(expanduser(path))


def _prepare_path(path):
    make_folder(dirname(remove_safely(path)))
    return path


def _prepare_suffix(suffix, length):
    if length < _MINIMUM_UNIQUE_LENGTH:
        raise ValueError(
            'length must be greater than %s' % _MINIMUM_UNIQUE_LENGTH)
    return make_random_string(length - _MINIMUM_UNIQUE_LENGTH) + suffix


def _process_folder(source_folder, excludes, write_path):
    for root_folder, folders, names in walk(source_folder, followlinks=True):
        for source_name in folders + names:
            if has_name_match(source_name, excludes):
                continue
            source_path = join(root_folder, source_name)
            target_path = relpath(source_path, source_folder)
            write_path(realpath(source_path), target_path)


tempfile._name_sequence = _CustomRandomNameSequence()
