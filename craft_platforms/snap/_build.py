# This file is part of craft-platforms.
#
# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Snapcraft-specific platforms information."""

import re
import typing
from collections.abc import Sequence

from craft_platforms import _architectures, _buildinfo, _distro, _errors, _platforms

CORE16_18_DEFAULT_ARCHITECTURES = (
    _architectures.DebianArchitecture.AMD64,
    _architectures.DebianArchitecture.ARM64,
    _architectures.DebianArchitecture.ARMHF,
    _architectures.DebianArchitecture.I386,
    _architectures.DebianArchitecture.PPC64EL,
    _architectures.DebianArchitecture.S390X,
)

CORE20_DEFAULT_ARCHITECTURES = (
    _architectures.DebianArchitecture.AMD64,
    _architectures.DebianArchitecture.ARM64,
    _architectures.DebianArchitecture.ARMHF,
    _architectures.DebianArchitecture.PPC64EL,
    _architectures.DebianArchitecture.S390X,
)

DEFAULT_ARCHITECTURES_BY_BASE = {
    "core": CORE16_18_DEFAULT_ARCHITECTURES,
    "core16": CORE16_18_DEFAULT_ARCHITECTURES,
    "core18": CORE16_18_DEFAULT_ARCHITECTURES,
    "core20": CORE20_DEFAULT_ARCHITECTURES,
}

# The default architectures if not otherwise specified for a base.
DEFAULT_ARCHITECTURES = (
    _architectures.DebianArchitecture.AMD64,
    _architectures.DebianArchitecture.ARM64,
    _architectures.DebianArchitecture.ARMHF,
    _architectures.DebianArchitecture.PPC64EL,
    _architectures.DebianArchitecture.RISCV64,
    _architectures.DebianArchitecture.S390X,
)

CORE_BASE_REGEX = re.compile("^core(?P<version>16|18|[2-9][02468])?$")

SNAP_TYPES_WITHOUT_BASE = ("base", "kernel", "snapd")

BASE_SNAPS_DOC_URL = (
    "https://canonical-snapcraft.readthedocs-hosted.com/en/stable/reference/bases/"
)


def get_default_architectures(base: str) -> Sequence[_architectures.DebianArchitecture]:
    if base in DEFAULT_ARCHITECTURES_BY_BASE:
        return DEFAULT_ARCHITECTURES_BY_BASE[base]
    return DEFAULT_ARCHITECTURES


def get_distro_base_from_core_base(base: str) -> _distro.DistroBase:
    """Get a DistroBase from the existing snap."""
    if base == "core":
        return _distro.DistroBase("ubuntu", "16.04")
    if match := CORE_BASE_REGEX.match(base):
        version = match.group("version")
        return _distro.DistroBase("ubuntu", f"{version}.04")
    return _distro.DistroBase.from_str(base)


def get_snap_base(
    *, base: str | None, build_base: str | None, snap_type: str | None
) -> _distro.DistroBase:
    if not base:
        if snap_type not in SNAP_TYPES_WITHOUT_BASE:
            raise _errors.RequiresBaseError(
                f"snaps of type {snap_type!r} require a 'base'",
                resolution="Declare a 'base' in 'snapcraft.yaml'",
                docs_url=BASE_SNAPS_DOC_URL,
            )
        if build_base == "devel" and snap_type != "base":
            raise _errors.RequiresBaseError(
                "non-base snaps require a 'base' if 'build-base' is 'devel",
                resolution="Declare a 'base' in 'snapcraft.yaml'",
                docs_url=BASE_SNAPS_DOC_URL,
            )
        if not build_base:
            raise _errors.RequiresBaseError(
                f"{snap_type!r} snaps require a 'build-base' if no 'base' is declared",
                resolution="Declare a 'build-base' in 'snapcraft.yaml'",
                docs_url=BASE_SNAPS_DOC_URL,
            )
        try:
            return get_distro_base_from_core_base(build_base)
        except ValueError:
            raise _errors.InvalidBaseError(
                build_base,
                build_base=True,
                resolution="Provide a valid 'build-base'",
                docs_url=BASE_SNAPS_DOC_URL,
            )
    if CORE_BASE_REGEX.match(base):
        if not build_base:
            return get_distro_base_from_core_base(base)
        if build_base == "devel":
            return _distro.DistroBase("ubuntu", "devel")
        if CORE_BASE_REGEX.match(build_base):
            raise _errors.InvalidBaseError(
                build_base,
                build_base=True,
                message="cannot specify a core 'build-base' alongside a 'base'",
                docs_url=BASE_SNAPS_DOC_URL,
            )
        if snap_type != "kernel":
            raise _errors.InvalidBaseError(
                build_base,
                build_base=True,
                message="non-kernel snaps cannot use 'base: coreXY' and arbitrary build-bases",
                docs_url=BASE_SNAPS_DOC_URL,
            )
        return _distro.DistroBase.from_str(build_base)
    if not build_base:
        raise _errors.InvalidBaseError(
            base,
            message="must declare a 'build-base' if 'base' does not match 'coreXY'",
            resolution="Provide a 'build-base'.",
            docs_url=BASE_SNAPS_DOC_URL,
        )
    try:
        return get_distro_base_from_core_base(build_base)
    except ValueError:
        raise _errors.InvalidBaseError(
            build_base,
            build_base=True,
            resolution="Ensure the build-base is supported.",
            docs_url=BASE_SNAPS_DOC_URL,
        )


@typing.overload
def get_platforms_snap_build_plan(
    base: None,
    *,
    platforms: _platforms.Platforms | None,
    build_base: str | None = None,
    snap_type: typing.Literal["base", "kernel"],
) -> Sequence[_buildinfo.BuildInfo]: ...
@typing.overload
def get_platforms_snap_build_plan(
    base: str,
    *,
    platforms: _platforms.Platforms | None,
    build_base: str | None = None,
    snap_type: str | None = None,
) -> Sequence[_buildinfo.BuildInfo]: ...
def get_platforms_snap_build_plan(
    base: str | None,
    *,
    platforms: _platforms.Platforms | None,
    build_base: str | None = None,
    snap_type: str | None = None,
) -> Sequence[_buildinfo.BuildInfo]:
    """Generate the build plan for a platforms-based charm."""
    distro_base = get_snap_base(base=base, build_base=build_base, snap_type=snap_type)
    if not platforms:
        platforms = {
            arch: None
            for arch in get_default_architectures(base or build_base or "default")
        }
    return _platforms.get_platforms_build_plan(distro_base, platforms)
