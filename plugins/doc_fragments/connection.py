# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


class ModuleDocFragment:
    DOCUMENTATION = r"""
options:
  url:
    description: Base URL of the Nexus server, for example C(https://nexus.example.com).
    type: str
    required: true
  username:
    description: User name used to authenticate against Nexus.
    type: str
    required: true
  password:
    description: Password of the user.
    type: str
    required: true
  validate_certs:
    description: Whether to validate the TLS certificate of the Nexus server.
    type: bool
    default: true
"""
