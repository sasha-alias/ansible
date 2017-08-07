#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2013, Evgenii Terechkov
# Written by Evgenii Terechkov <evg@altlinux.org>
# Based on urpmi module written by Philippe Makowski <philippem@mageia.org>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: apt_rpm
short_description: apt_rpm package manager
description:
  - Manages packages with I(apt-rpm). Both low-level (I(rpm)) and high-level (I(apt-get)) package manager binaries required.
version_added: "1.5"
options:
  pkg:
    description:
      - name of package to install, upgrade or remove.
    required: true
    default: null
  state:
    description:
      - Indicates the desired package state
    required: false
    default: present
    choices: [ "absent", "present" ]
  update_cache:
    description:
      - update the package database first C(apt-get update).
    required: false
    default: no
    choices: [ "yes", "no" ]
author: "Evgenii Terechkov (@evgkrsk)"
notes:  []
'''

EXAMPLES = '''
# install package foo
- apt_rpm:
    pkg: foo
    state: present

# remove package foo
- apt_rpm:
    pkg: foo
    state: absent

# description: remove packages foo and bar
- apt_rpm:
    pkg: foo,bar
    state: absent

# description: update the package database and install bar (bar will be the updated if a newer version exists)
- apt_rpm:
    name: bar
    state: present
    update_cache: yes
'''


try:
    import json
except ImportError:
    import simplejson as json

import shlex
import os
import sys

APT_PATH="/usr/bin/apt-get"
RPM_PATH="/usr/bin/rpm"

def query_package(module, name):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    rc, out, err = module.run_command("%s -q %s" % (RPM_PATH,name))
    if rc == 0:
        return True
    else:
        return False

def query_package_provides(module, name):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    rc, out, err = module.run_command("%s -q --provides %s" % (RPM_PATH,name))
    return rc == 0

def update_package_db(module):
    rc, out, err = module.run_command("%s update" % APT_PATH)

    if rc != 0:
        module.fail_json(msg="could not update package db: %s" % err)

def remove_packages(module, packages):

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package):
            continue

        rc, out, err = module.run_command("%s -y remove %s" % (APT_PATH,package))

        if rc != 0:
            module.fail_json(msg="failed to remove %s: %s" % (package, err))

        remove_c += 1

    if remove_c > 0:
        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pkgspec):

    packages = ""
    for package in pkgspec:
        if not query_package_provides(module, package):
            packages += "'%s' " % package

    if len(packages) != 0:

        rc, out, err = module.run_command("%s -y install %s" % (APT_PATH, packages))

        installed = True
        for packages in pkgspec:
            if not query_package_provides(module, package):
                installed = False

        # apt-rpm always have 0 for exit code if --force is used
        if rc or not installed:
            module.fail_json(msg="'apt-get -y install %s' failed: %s" % (packages, err))
        else:
            module.exit_json(changed=True, msg="%s present(s)" % packages)
    else:
        module.exit_json(changed=False)


def main():
    module = AnsibleModule(
        argument_spec    = dict(
            state        = dict(default='installed', choices=['installed', 'removed', 'absent', 'present']),
            update_cache = dict(default=False, aliases=['update-cache'], type='bool'),
            package      = dict(aliases=['pkg', 'name'], required=True)))


    if not os.path.exists(APT_PATH) or not os.path.exists(RPM_PATH):
        module.fail_json(msg="cannot find /usr/bin/apt-get and/or /usr/bin/rpm")

    p = module.params

    if p['update_cache']:
        update_package_db(module)

    packages = p['package'].split(',')

    if p['state'] in [ 'installed', 'present' ]:
        install_packages(module, packages)

    elif p['state'] in [ 'removed', 'absent' ]:
        remove_packages(module, packages)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
