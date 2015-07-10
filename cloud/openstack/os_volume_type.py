#!/usr/bin/python

# Copyright (c) 2015 Blue Box Group, Inc.
# Copyright (c) 2015, Jesse Keating <jkeating@j2solutions.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


DOCUMENTATION = '''
---
module: os_volume_type
short_description: Create/Delete Cinder Volume Types
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Jesse Keating (@iamjkeating)"
description:
   - Create or Remove cinder block storage volume types
options:
   name:
     description:
        - Name of volume type
     required: true
   display_description:
     description:
       - String describing the volume type
     required: false
     default: None
   is_public:
     description:
       - Flag indicating whether this is a public type or not
     required: false
     default: true
   encryption_type:
     description:
        - flag indicating whether this is an encrypted volume type
     required: false
     default: false
   provider:
     description:
        - The class that provides encryption support
     required: only when encryption_type is true
     default: None
   cipher:
     description:
        - The encryption algorithm or mode
     required: false
     default: None
   key_size:
     description:
        - Size of encryption key in bits
     required: false
     default: None
   control_location:
     description:
        - Notional service where encryption is performed
     choices: [front-end, back-end]
     required: false
     default: front-end
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
     - "python >= 2.6"
     - "shade"
'''

EXAMPLES = '''
# Creates a new volume type
- name: create a volume type
  hosts: localhost
  tasks:
  - name: create LVM volume type
    os_volume_type:
      state: present
      cloud: bluebox
      name: LVM

# Creates a new encrypted volume type
- name: create a LUKS volume type
  hosts: localhost
  tasks:
  - name: create LUKS volume type
    os_volume_type:
      state: present
      cloud: bluebox
      name: LUKS
      encryption_type: true
      cipher: aes-xts-plain64
      key_size: 1024
      provider: nova.volume.encryptors.luks.LuksEncryptor
'''


def _present_volume_type(module, cloud):
    if cloud.volume_type_exists(module.params['display_name']):
        t = cloud.get_volume_type(module.params['display_name'])
        module.exit_json(changed=False, id=v['id'], volume_type=t)

    volume_args = dict(
        size=module.params['size'],
        volume_type=module.params['volume_type'],
        display_name=module.params['display_name'],
        display_description=module.params['display_description'],
        snapshot_id=module.params['snapshot_id'],
        availability_zone=module.params['availability_zone'],
    )
    if module.params['image']:
        image_id = cloud.get_image_id(module.params['image'])
        volume_args['imageRef'] = image_id

    volume = cloud.create_volume(
        wait=module.params['wait'], timeout=module.params['timeout'],
        **volume_args)
    module.exit_json(changed=True, id=volume['id'], volume=volume)


def _absent_volume(module, cloud):
    try:
        cloud.delete_volume(
            name_or_id=module.params['display_name'],
            wait=module.params['wait'],
            timeout=module.params['timeout'])
    except shade.OpenStackCloudTimeout:
        module.exit_json(changed=False)
    module.exit_json(changed=True)


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(default=None),
        display_description=dict(default=None),
        is_public=dict(default=True, type='bool'),
        encryption_type=dict(default=False, type='bool'),
        provider=dict(default=None),
        cipher=dict(default=None),
        key_size=dict(default=None, type='int'),
        control_location=dict(default='front-end', choices=['front-end',
                                                            'back-end']),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module = AnsibleModule(argument_spec=argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']

    encryption = module.params['encryption_type']

    if encryption and not module.params['provider']:
        module.fail_json(msg=("provider is required when encryption_type is "
                              "'true'"))

    try:
        cloud = shade.openstack_cloud(**module.params)
        if state == 'present':
            _present_volume_type(module, cloud)
        if state == 'absent':
            _absent_volume_type(module, cloud)
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
