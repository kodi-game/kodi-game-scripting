#!/usr/bin/env python3

# Copyright (C) 2016-2018 Christian Fetzer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

""" Test common utility functions """

import collections

from unittest import mock

import pytest

from kodi_game_scripting import utils


# pylint: disable=redefined-outer-name

@pytest.fixture()
def ensure_directory_exists_fixture(mocker):
    """Mock file access methods for ensure_directory_exists tests"""
    return (mocker.patch('os.path.exists'),
            mocker.patch('os.makedirs'),
            mocker.patch('shutil.rmtree'))


@pytest.mark.parametrize('clean', [False, True])
def test_ensuredirectoryexists_create(ensure_directory_exists_fixture, clean):
    """Test ensure_directory_exists with non existent target directory"""
    mock_exists, mock_makedirs, mock_rmtree = ensure_directory_exists_fixture
    mock_exists.return_value = False
    utils.ensure_directory_exists('/foo', clean)
    mock_rmtree.assert_not_called()
    mock_makedirs.assert_called_once_with('/foo')


def test_ensuredirectoryexists_noop(ensure_directory_exists_fixture):
    """Test ensure_directory_exists with existent target directory"""
    mock_exists, mock_makedirs, mock_rmtree = ensure_directory_exists_fixture
    mock_exists.return_value = True
    utils.ensure_directory_exists('/foo')
    mock_rmtree.assert_not_called()
    mock_makedirs.assert_not_called()


def test_ensuredirectoryexists_recreate(ensure_directory_exists_fixture):
    """Test ensure_directory_exists with recreating the target directory"""
    mock_exists, mock_makedirs, mock_rmtree = ensure_directory_exists_fixture
    mock_exists.side_effect = [True, False]
    utils.ensure_directory_exists('/foo', clean=True)
    mock_rmtree.assert_called_once_with('/foo')
    mock_makedirs.assert_called_once_with('/foo')


def test_ensuredirectoryexists_ignore_oserror(ensure_directory_exists_fixture):
    """Test ensure_directory_exists ignores OSError"""
    mock_exists, _, mock_rmtree = ensure_directory_exists_fixture
    mock_exists.return_value = True
    mock_rmtree.side_effect = OSError
    utils.ensure_directory_exists('/foo', clean=True)


@mock.patch('os.walk')
def test_list_all_files(mock_walk):
    """Test list_all_files function"""
    mock_walk.return_value = [
        ('/foo', ('bar',), ('baz',)),
        ('/foo/bar', (), ('test1', 'test2')),
    ]
    assert utils.list_all_files('/foo') == ['baz', 'bar/test1', 'bar/test2']


def test_purify():
    """Test purify function"""
    assert utils.purify(['test', [None, None]]) == ['test']
    assert utils.purify({'l1': {'l2': 'v2'}, 'l3': {}}) == {'l1': {'l2': 'v2'}}
    assert utils.purify({'l1': [{}, {}], 'l2': {}}) == {}
    assert utils.purify([]) == []
    assert utils.purify(collections.OrderedDict()) == collections.OrderedDict()


def test_xstr():
    """Test xstr conversion"""
    assert utils.xstr(b'test') == 'test'
    assert utils.xstr(None) == ''
