#!/usr/bin/python
# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: repository_composer
short_description: Manage Nexus Composer repositories
version_added: 0.2.0
description:
  - Create, update or delete a Nexus repository of the C(composer) format.
  - Supports the C(hosted), C(proxy) and C(group) repository types.
author:
  - Amirhosein Shaerpour (@shaerpour)
extends_documentation_fragment:
  - shaerpour.nexus.connection
options:
  name:
    description: Name of the repository.
    type: str
    required: true
  state:
    description:
      - C(present) creates the repository, or updates it when its settings differ.
      - C(absent) deletes the repository.
    type: str
    choices: [present, absent]
    default: present
  type:
    description:
      - Type of the repository.
      - C(hosted) stores content in Nexus.
      - C(proxy) caches content of a remote repository.
      - C(group) serves the content of several other repositories under one URL.
      - The type of an existing repository cannot be changed.
    type: str
    choices: [hosted, proxy, group]
    default: hosted
  online:
    description: Whether the repository accepts requests.
    type: bool
    default: true
  blob_store:
    description: Name of the blob store that holds the repository content.
    type: str
    default: default
  strict_content_type_validation:
    description: Whether to validate that the content type matches the file extension.
    type: bool
    default: true
  write_policy:
    description:
      - Whether existing content can be redeployed.
      - Only used when I(type=hosted).
    type: str
    choices: [allow, allow_once, deny]
    default: allow_once
  remote_url:
    description:
      - URL of the remote repository to proxy.
      - Required when I(type=proxy).
    type: str
  content_max_age:
    description:
      - Minutes to cache content before checking the remote again.
      - Only used when I(type=proxy).
    type: int
    default: 1440
  metadata_max_age:
    description:
      - Minutes to cache metadata before checking the remote again.
      - Only used when I(type=proxy).
    type: int
    default: 1440
  members:
    description:
      - Names of the repositories in the group, in lookup order.
      - Required when I(type=group).
    type: list
    elements: str
"""

EXAMPLES = r"""
- name: Create a hosted Composer repository
  shaerpour.nexus.repository_composer:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: composer-hosted

- name: Create a proxy Composer repository
  shaerpour.nexus.repository_composer:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: composer-proxy
    type: proxy
    remote_url: https://repo.packagist.org

- name: Create a group Composer repository
  shaerpour.nexus.repository_composer:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: composer-group
    type: group
    members:
      - composer-hosted
      - composer-proxy

- name: Delete a repository
  shaerpour.nexus.repository_composer:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: composer-hosted
    state: absent
"""

RETURN = r""" # """

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.shaerpour.nexus.plugins.module_utils.client import (
    AUTH_ARGUMENT_SPEC,
    NexusClient,
    NexusError,
)

# Nexus caches "not found" answers from the remote of a proxy repository for this many minutes.
NEGATIVE_CACHE_TTL = 1440


def build_payload(params):
    """Build the request body that Nexus expects for the requested repository."""
    storage = {
        "blobStoreName": params["blob_store"],
        "strictContentTypeValidation": params["strict_content_type_validation"],
    }
    payload = {"name": params["name"], "online": params["online"], "storage": storage}

    if params["type"] == "hosted":
        storage["writePolicy"] = params["write_policy"].upper()
    elif params["type"] == "proxy":
        payload["proxy"] = {
            "remoteUrl": params["remote_url"],
            "contentMaxAge": params["content_max_age"],
            "metadataMaxAge": params["metadata_max_age"],
        }
        payload["negativeCache"] = {"enabled": True, "timeToLive": NEGATIVE_CACHE_TTL}
        payload["httpClient"] = {"blocked": False, "autoBlock": True}
    else:
        payload["group"] = {"memberNames": params["members"]}

    return payload


def is_subset(desired, current):
    """Return True when every value in ``desired`` is also set in ``current``.

    Nexus returns more fields than we send (``url``, ``format``, ...), so only
    the fields we manage are compared.
    """
    if isinstance(desired, dict):
        return all(key in current and is_subset(value, current[key]) for key, value in desired.items())
    return desired == current


def ensure_absent(client, name, current, check_mode):
    """Delete the repository if it exists. Return True when something changed."""
    if current is None:
        return False
    if not check_mode:
        client.request("DELETE", f"/repositories/{name}")
    return True


def ensure_present(client, params, current, check_mode):
    """Create the repository, or update it when it differs. Return True when something changed."""
    collection_path = f"/repositories/composer/{params['type']}"
    payload = build_payload(params)

    if current is None:
        if not check_mode:
            client.request("POST", collection_path, payload)
        return True

    if is_subset(payload, current):
        return False
    if not check_mode:
        client.request("PUT", f"{collection_path}/{params['name']}", payload)
    return True


def ensure(client, params, check_mode):
    """Bring the repository to the requested state. Return True when something changed."""
    name = params["name"]
    current = client.request("GET", f"/repositories/composer/{params['type']}/{name}")

    if params["state"] == "absent":
        return ensure_absent(client, name, current, check_mode)
    return ensure_present(client, params, current, check_mode)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **AUTH_ARGUMENT_SPEC,
            name=dict(type="str", required=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            type=dict(type="str", default="hosted", choices=["hosted", "proxy", "group"]),
            online=dict(type="bool", default=True),
            blob_store=dict(type="str", default="default"),
            strict_content_type_validation=dict(type="bool", default=True),
            write_policy=dict(type="str", default="allow_once", choices=["allow", "allow_once", "deny"]),
            remote_url=dict(type="str"),
            content_max_age=dict(type="int", default=1440),
            metadata_max_age=dict(type="int", default=1440),
            members=dict(type="list", elements="str"),
        ),
        required_if=[
            ("type", "proxy", ["remote_url"]),
            ("type", "group", ["members"]),
        ],
        supports_check_mode=True,
    )
    params = module.params
    client = NexusClient(params["url"], params["username"], params["password"], params["validate_certs"])

    try:
        changed = ensure(client, params, module.check_mode)
    except NexusError as error:
        module.fail_json(msg=str(error))

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
