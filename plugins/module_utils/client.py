# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json

from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url

API_PATH = "/service/rest/v1"

AUTH_ARGUMENT_SPEC = dict(
    url=dict(type="str", required=True),
    username=dict(type="str", required=True),
    password=dict(type="str", required=True, no_log=True),
    validate_certs=dict(type="bool", default=True),
)


class NexusError(Exception):
    pass


class NexusClient:
    def __init__(self, url, username, password, validate_certs=True):
        self.base = url.rstrip("/") + API_PATH
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.username = username
        self.password = password
        self.validate_certs = validate_certs

    def request(self, method, path, data=None):
        """Return the decoded JSON body, or None for an empty body or a 404."""
        body = None if data is None else json.dumps(data)
        try:
            response = open_url(
                self.base + path,
                method=method,
                data=body,
                headers=self.headers,
                url_username=self.username,
                url_password=self.password,
                force_basic_auth=True,
                validate_certs=self.validate_certs,
            )
        except HTTPError as e:
            if e.code == 404:
                return None
            raise NexusError(f"{method} {path} failed: {e.code} {e.read().decode()}") from e
        content = response.read()
        return json.loads(content) if content else None
