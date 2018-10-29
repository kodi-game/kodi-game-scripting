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

""" Test credentials """

import pytest

from kodi_game_scripting.credentials import Credentials

pytestmark = [pytest.mark.unit]


# pylint: disable=redefined-outer-name

@pytest.fixture
def keyring_fixture(mocker):
    """ Setup test to get password from keyring """
    mocker.patch('keyring.get_password', side_effect=['user', 'pass', 'user'])


@pytest.fixture
def getpass_fixture(mocker):
    """ Setup test to get password from getpass """
    mocker.patch('keyring.get_password', return_value='')
    mocker.patch('getpass.getuser', return_value='user')
    mocker.patch('getpass.getpass', return_value='pass')
    mocker.patch('builtins.input', return_value='user')


@pytest.mark.parametrize('fixture', ['keyring_fixture', 'getpass_fixture'])
def test_credentials_keyring(fixture, request, mocker):
    """ Test credentials from system keyring """
    request.getfixturevalue(fixture)
    set_password = mocker.patch('keyring.set_password', autospec=True)
    cred = Credentials('test')
    assert cred.load() == ('user', 'pass')
    cred.save('user', 'pass')
    set_password.assert_has_calls([
        mocker.call('test_username', '_username', 'user'),
        mocker.call('test_password', 'user', 'pass')])
    cred.clean()
    set_password.assert_has_calls([
        mocker.call('test_username', '_username', ''),
        mocker.call('test_password', 'user', '')])


def test_credentials_none(mocker):
    """ Test credentials from system getpass """
    mocker.patch('keyring.get_password', return_value=None)
    mocker.patch('builtins.input', return_value=None)
    mocker.patch('getpass.getuser', return_value='')
    cred = Credentials('test')
    assert cred.load() == ('', '')
