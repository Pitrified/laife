"""The vendor manifest, the integrity checks, the extraction and the /vendor route.

No network: every tarball here is built in memory. The real manifest is parsed
and checked against the page's import map, never fetched.
"""

import asyncio
from dataclasses import dataclass
import io
import json
import re
import tarfile
from typing import TYPE_CHECKING

import httpx
import pytest

from laife.headless import build_world
from laife.params.laife_params import get_laife_params
from laife.web.events import EventHub
from laife.web.server import PAGE_NAME
from laife.web.server import create_app
from laife.web.vendor import LOCK_NAME
from laife.web.vendor import NpmPackage
from laife.web.vendor import UnsafeArchiveMemberError
from laife.web.vendor import UnsafeUrlError
from laife.web.vendor import VendorFileMissingError
from laife.web.vendor import VendorIntegrityError
from laife.web.vendor import download
from laife.web.vendor import extract_package
from laife.web.vendor import load_manifest
from laife.web.vendor import package_is_current
from laife.web.vendor import sha256_hex
from laife.web.vendor import sri_digest
from laife.web.vendor import verified_path

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class FakePackage:
    """A tarball built in memory and the pin that matches it."""

    pkg: NpmPackage
    tarball: bytes


def make_tarball(files: dict[str, bytes]) -> bytes:
    """Return a .tgz with *files* under ``package/``, as npm packs them."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(f"package/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


@pytest.fixture
def fake() -> FakePackage:
    """Return a package with one listed file and one that is not listed."""
    tarball = make_tarball({"dist/lib.mjs": b"export const x = 1;\n", "README.md": b"readme"})
    pkg = NpmPackage(
        name="fake-lib",
        version="1.0.0",
        integrity=sri_digest(tarball, "sha512"),
        files=("dist/lib.mjs",),
    )
    return FakePackage(pkg, tarball)


def cached(tmp_path: Path, fake: FakePackage) -> Path:
    """Fill a cache with *fake*, laid out as ``ensure_vendor`` lays it out."""
    extract_package(fake.pkg, fake.tarball, tmp_path / fake.pkg.folder_name)
    return tmp_path


def test_real_manifest_pins_what_the_page_imports() -> None:
    """Every target of the page's import map is a file the manifest lists."""
    manifest = load_manifest()
    page = (get_laife_params().paths.ui_fol / PAGE_NAME / "index.html").read_text()
    found = re.search(r'<script type="importmap">(.*?)</script>', page, re.DOTALL)
    assert found is not None, "the page has no import map"
    import_map = json.loads(found.group(1))
    targets = list(import_map["imports"].values())
    assert targets
    for url in targets:
        package, member = url.removeprefix("/vendor/").split("/", maxsplit=1)
        pkg = manifest.package(package)
        assert member in pkg.files
        assert pkg.integrity.startswith("sha512-")


def test_extract_writes_only_listed_files_and_a_lock(tmp_path: Path, fake: FakePackage) -> None:
    """Listed files come out with their hashes recorded; the rest stay packed."""
    lock = extract_package(fake.pkg, fake.tarball, tmp_path)
    assert set(lock) == {"dist/lib.mjs"}
    assert (tmp_path / "dist" / "lib.mjs").read_bytes() == b"export const x = 1;\n"
    assert not (tmp_path / "README.md").exists()
    assert json.loads((tmp_path / LOCK_NAME).read_text()) == lock
    assert package_is_current(fake.pkg, tmp_path)


def test_extract_refuses_a_tarball_that_does_not_match(tmp_path: Path, fake: FakePackage) -> None:
    """A tarball whose hash differs from the pin extracts nothing."""
    other = make_tarball({"dist/lib.mjs": b"export const x = 2;\n"})
    with pytest.raises(VendorIntegrityError, match="fake-lib"):
        extract_package(fake.pkg, other, tmp_path)
    assert not (tmp_path / "dist").exists()


def test_extract_names_a_missing_member(tmp_path: Path, fake: FakePackage) -> None:
    """A manifest listing a file the package does not ship fails by name."""
    pkg = NpmPackage(fake.pkg.name, fake.pkg.version, fake.pkg.integrity, ("dist/gone.mjs",))
    with pytest.raises(VendorFileMissingError, match=r"gone\.mjs"):
        extract_package(pkg, fake.tarball, tmp_path)


def test_verified_path_refuses_an_edited_cache(tmp_path: Path, fake: FakePackage) -> None:
    """An intact file resolves; the same file changed after extraction is refused."""
    cache = cached(tmp_path, fake)
    path = verified_path(fake.pkg, "dist/lib.mjs", cache)
    path.write_bytes(b"export const x = 666;\n")
    with pytest.raises(VendorIntegrityError):
        verified_path(fake.pkg, "dist/lib.mjs", cache)


def test_verified_path_refuses_unlisted_files(tmp_path: Path, fake: FakePackage) -> None:
    """Only manifest files are served, even when something else sits in the folder."""
    cache = cached(tmp_path, fake)
    (cache / fake.pkg.folder_name / "extra.js").write_text("x")
    with pytest.raises(VendorFileMissingError):
        verified_path(fake.pkg, "extra.js", cache)


def test_manifest_refuses_paths_that_leave_the_package(tmp_path: Path) -> None:
    """A manifest cannot name a file outside its package's folder."""
    manifest = tmp_path / "vendor.toml"
    manifest.write_text(
        '[npm.bad]\nversion = "1"\nintegrity = "sha512-x"\nfiles = ["../escape.js"]\n'
    )
    with pytest.raises(UnsafeArchiveMemberError):
        load_manifest(manifest)


def test_download_refuses_plain_http() -> None:
    """Nothing is fetched over plain http."""
    with pytest.raises(UnsafeUrlError):
        download("http://registry.npmjs.org/x")


def test_route_serves_checked_files_only(tmp_path: Path) -> None:
    """/vendor serves a cached, intact manifest file; refuses an edited one; 404s the rest."""
    manifest = load_manifest()
    pkg = manifest.packages[0]
    member = pkg.files[0]
    folder = tmp_path / pkg.folder_name
    (folder / member).parent.mkdir(parents=True)
    (folder / member).write_bytes(b"export {};\n")
    (folder / LOCK_NAME).write_text(json.dumps({member: sha256_hex(b"other bytes")}))

    async def get(app_path: str) -> httpx.Response:
        app = create_app(build_world(0, None), None, EventHub(), vendor_cache=tmp_path)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(app_path)

    # The lock above does not match the bytes: refused.
    response = asyncio.run(get(f"/vendor/{pkg.name}/{member}"))
    assert response.status_code == httpx.codes.INTERNAL_SERVER_ERROR
    assert "Integrity check failed" in response.json()["detail"]

    # A matching lock: served, as JavaScript, not cached without asking.
    (folder / LOCK_NAME).write_text(json.dumps({member: sha256_hex(b"export {};\n")}))
    response = asyncio.run(get(f"/vendor/{pkg.name}/{member}"))
    assert response.status_code == httpx.codes.OK
    assert "javascript" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache"

    assert asyncio.run(get(f"/vendor/{pkg.name}/package.json")).status_code == httpx.codes.NOT_FOUND
    assert asyncio.run(get("/vendor/not-a-package/x.js")).status_code == httpx.codes.NOT_FOUND
