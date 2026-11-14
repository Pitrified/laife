"""Third-party files for the page: a manifest in git, a checked cache outside it.

The manifest, ``ui/vendor.toml``, pins every npm package by exact version and by
the integrity hash the npm registry publishes for its tarball, and lists the
files to take from it. :func:`ensure_vendor` downloads what is missing into
``cache/vendor/``, refuses a tarball whose hash does not match, and extracts
only the listed files.

npm publishes one hash per tarball, not per file, so each extracted file is
recorded in a lock beside it with its own sha256. The server checks a file
against that lock before sending it (:func:`verified_path`), so a cache edited
after the fact is refused rather than served.

The same scheme as abyss's ``abyss.ui.vendor``, without its plain-file pins.
Run as ``python -m laife.web.vendor``, which is what ``make vendor`` does.
"""

import base64
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tomllib
import urllib.request

from loguru import logger as lg

from laife.params.laife_params import get_laife_params

NPM_REGISTRY = "https://registry.npmjs.org"
LOCK_NAME = "files.lock.json"
DOWNLOAD_TIMEOUT_S = 120.0


class VendorIntegrityError(RuntimeError):
    """Downloaded or cached bytes do not match their pinned hash."""

    def __init__(self, what: str, expected: str, actual: str) -> None:
        """Name the item and both hashes, and say what to do."""
        super().__init__(
            f"Integrity check failed for {what}: expected {expected}, got {actual}. "
            "Delete the cached copy and run `make vendor` again; if it fails "
            "again, the pin in ui/vendor.toml is wrong or the source changed."
        )


class VendorFileMissingError(FileNotFoundError):
    """A file was asked for that the manifest or the cache does not have."""

    def __init__(self, name: str, member: str | None = None) -> None:
        """Name the package and, when one was asked for, the file in it."""
        what = f"{name}/{member}" if member else name
        super().__init__(
            f"{what!r} is not in the manifest or not in the vendor cache. "
            "Check ui/vendor.toml, then run `make vendor`."
        )


class UnsafeUrlError(ValueError):
    """A URL to fetch is not plain https."""

    def __init__(self, url: str) -> None:
        """Name the URL."""
        super().__init__(f"Only https URLs are fetched, got {url!r}")


class UnsafeArchiveMemberError(ValueError):
    """The manifest names a path that leaves its package folder."""

    def __init__(self, name: str) -> None:
        """Name the path."""
        super().__init__(f"Refusing archive path {name!r}: it leaves the package folder")


@dataclass(frozen=True)
class NpmPackage:
    """One npm package pinned in the manifest."""

    name: str
    version: str
    integrity: str
    files: tuple[str, ...]

    @property
    def tarball_url(self) -> str:
        """Return the registry URL of the tarball, scoped names included."""
        basename = self.name.rsplit("/", maxsplit=1)[-1]
        return f"{NPM_REGISTRY}/{self.name}/-/{basename}-{self.version}.tgz"

    @property
    def folder_name(self) -> str:
        """Return the cache folder name, with the version, safe for a filesystem."""
        return f"{self.name.replace('/', '__')}@{self.version}"


@dataclass(frozen=True)
class Manifest:
    """The parsed ``ui/vendor.toml``."""

    packages: tuple[NpmPackage, ...]

    def package(self, name: str) -> NpmPackage:
        """Return the package pinned as *name*.

        Raises:
            VendorFileMissingError: If the manifest does not list it.
        """
        for pkg in self.packages:
            if pkg.name == name:
                return pkg
        raise VendorFileMissingError(name)


def load_manifest(path: Path | None = None) -> Manifest:
    """Parse the manifest, ``ui/vendor.toml`` by default.

    Raises:
        UnsafeArchiveMemberError: If a listed file would leave its package.
    """
    path = path or get_laife_params().paths.vendor_manifest
    data = tomllib.loads(path.read_text())
    packages = []
    for name, spec in data.get("npm", {}).items():
        files = tuple(spec["files"])
        for member in files:
            if member.startswith("/") or ".." in Path(member).parts:
                raise UnsafeArchiveMemberError(member)
        packages.append(NpmPackage(name, spec["version"], spec["integrity"], files))
    return Manifest(tuple(packages))


def sri_digest(data: bytes, algorithm: str) -> str:
    """Hash *data* in the Subresource Integrity format npm uses, ``<algorithm>-<base64>``."""
    digest = hashlib.new(algorithm, data).digest()
    return f"{algorithm}-{base64.b64encode(digest).decode()}"


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex sha256 of *data*."""
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    """Fetch *url*, which must be https.

    Raises:
        UnsafeUrlError: If the URL is not https.
    """
    if not url.startswith("https://"):
        raise UnsafeUrlError(url)
    lg.info(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response:  # noqa: S310 - scheme checked above
        return response.read()


def extract_package(pkg: NpmPackage, tarball: bytes, dest: Path) -> dict[str, str]:
    """Check *tarball* against its pin, extract the listed files into *dest*, return the lock.

    The lock maps each extracted file to its sha256 and is written beside them.

    Raises:
        VendorIntegrityError: If the tarball does not match the pin.
        VendorFileMissingError: If a listed file is not in the tarball.
    """
    algorithm = pkg.integrity.split("-", maxsplit=1)[0]
    actual = sri_digest(tarball, algorithm)
    if actual != pkg.integrity:
        raise VendorIntegrityError(pkg.tarball_url, pkg.integrity, actual)
    lock = {}
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        for member_name in pkg.files:
            try:
                member = archive.getmember(f"package/{member_name}")
            except KeyError:
                raise VendorFileMissingError(pkg.name, member_name) from None
            handle = archive.extractfile(member)
            if handle is None:
                raise VendorFileMissingError(pkg.name, member_name)
            data = handle.read()
            target = dest / member_name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            lock[member_name] = sha256_hex(data)
    (dest / LOCK_NAME).write_text(json.dumps(lock, indent=1, sort_keys=True))
    return lock


def package_is_current(pkg: NpmPackage, folder: Path) -> bool:
    """Tell whether *folder* holds exactly the files the manifest lists for *pkg*."""
    lock_path = folder / LOCK_NAME
    if not lock_path.is_file():
        return False
    lock = json.loads(lock_path.read_text())
    return set(lock) == set(pkg.files) and all((folder / f).is_file() for f in lock)


def ensure_vendor(manifest: Manifest | None = None, cache: Path | None = None) -> None:
    """Download and check every package the manifest lists that is not cached yet."""
    manifest = manifest or load_manifest()
    cache = cache or get_laife_params().paths.vendor_fol
    for pkg in manifest.packages:
        folder = cache / pkg.folder_name
        if package_is_current(pkg, folder):
            lg.info(f"{pkg.name}@{pkg.version} already cached")
            continue
        extract_package(pkg, download(pkg.tarball_url), folder)
        lg.info(f"Cached {pkg.name}@{pkg.version}: {len(pkg.files)} files")


def verified_path(pkg: NpmPackage, member: str, cache: Path | None = None) -> Path:
    """Return the cached path of *member* of *pkg*, after checking it against the lock.

    Raises:
        VendorFileMissingError: If the file is not listed or not cached.
        VendorIntegrityError: If the cached bytes no longer match the lock.
    """
    cache = cache or get_laife_params().paths.vendor_fol
    folder = cache / pkg.folder_name
    lock_path = folder / LOCK_NAME
    if member not in pkg.files or not lock_path.is_file():
        raise VendorFileMissingError(pkg.name, member)
    expected = json.loads(lock_path.read_text()).get(member)
    path = folder / member
    if expected is None or not path.is_file():
        raise VendorFileMissingError(pkg.name, member)
    actual = sha256_hex(path.read_bytes())
    if actual != expected:
        raise VendorIntegrityError(str(path), expected, actual)
    return path


if __name__ == "__main__":
    ensure_vendor()
