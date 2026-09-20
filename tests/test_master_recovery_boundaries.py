"""Adversarial contracts for materialized recovery; no real providers or large bombs."""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import struct
import warnings
import zipfile

import pytest

from src.qa import master_recovery as recovery


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bundle(path, entries, *, compression=zipfile.ZIP_STORED):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", compression=compression) as archive:
            for name, data in entries:
                archive.writestr(name, data)
    return path


def contract(data, *, container_sha=None):
    return recovery.RecoveryContract(
        recovery.MasterIdentity("master", digest(data), len(data)),
        recovery.RecoveryCandidate("bundle", "local_file", "fixture:bundle",
            container_member="master.mp4", expected_container_sha256=container_sha),
    )


@pytest.mark.parametrize("field", ["max_member_bytes", "max_zip_entries", "max_compression_ratio"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_invalid_policy_is_rejected_before_candidate_read(tmp_path, field, value):
    path = bundle(tmp_path / "data.zip", [("master.mp4", b"x")])
    with pytest.raises(ValueError, match="positive|finite"):
        recovery.sha256_zip_member(path, "master.mp4", **{field: value})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, 1.5])
def test_container_byte_limit_must_be_positive_integer(tmp_path, value):
    path = tmp_path / "data.bin"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="positive integer"):
        recovery.sha256_path(path, max_bytes=value)


def test_entry_ceiling_is_applied_before_zipfile_allocation(tmp_path, monkeypatch):
    path = bundle(tmp_path / "many.zip", [("master.mp4", b"x"), ("a", b""), ("b", b"")])
    def forbidden(*args, **kwargs):
        raise AssertionError("ZipFile allocated metadata before enforcing entry limit")
    monkeypatch.setattr(zipfile, "ZipFile", forbidden)
    with pytest.raises(recovery.RecoveryLimitExceeded, match="zip_entry_count_exceeded"):
        recovery.sha256_zip_member(path, "master.mp4", max_zip_entries=2)


def test_lying_footer_cannot_bypass_entry_ceiling(tmp_path, monkeypatch):
    path = bundle(tmp_path / "lying.zip", [("master.mp4", b"x"), ("a", b""), ("b", b"")])
    data = bytearray(path.read_bytes())
    offset = data.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", data, offset + 8, 1, 1)
    path.write_bytes(data)
    def forbidden(*args, **kwargs):
        raise AssertionError("untrusted footer count permitted metadata allocation")
    monkeypatch.setattr(zipfile, "ZipFile", forbidden)
    with pytest.raises(recovery.RecoveryLimitExceeded, match="zip_entry_count_exceeded"):
        recovery.sha256_zip_member(path, "master.mp4", max_zip_entries=2)


def test_duplicate_member_never_gains_recovery_authority(tmp_path):
    good = b"master"
    path = bundle(tmp_path / "dupe.zip", [("master.mp4", b"wrong"), ("master.mp4", good)])
    result = recovery.verify_recovery(contract(good), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert result.authority == "NONE"
    assert not result.exact


@pytest.mark.parametrize("replace_inode", [False, True])
def test_container_and_member_must_come_from_same_file_revision(tmp_path, monkeypatch, replace_inode):
    good, wrong = b"master-correct", b"master-INVALID"
    path = bundle(tmp_path / "candidate.zip", [("master.mp4", wrong)])
    replacement = bundle(tmp_path / "replacement.zip", [("master.mp4", good)])
    expected_container = digest(path.read_bytes())
    original = zipfile.ZipFile
    def swapped(*args, **kwargs):
        if replace_inode:
            replacement.replace(path)
        else:
            path.write_bytes(replacement.read_bytes())
        return original(*args, **kwargs)
    monkeypatch.setattr(zipfile, "ZipFile", swapped)
    result = recovery.verify_recovery(contract(good, container_sha=expected_container), path)
    assert result.authority == "NONE", "container hash from A must not authenticate member from B"
    assert not result.exact


def test_symlink_member_is_not_media(tmp_path):
    entry = zipfile.ZipInfo("master.mp4")
    entry.create_system = 3
    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
    data = b"/etc/passwd"
    path = bundle(tmp_path / "symlink.zip", [(entry, data)])
    result = recovery.verify_recovery(contract(data), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert not result.exact


def test_unsupported_compression_returns_typed_failure(tmp_path):
    good = b"master"
    path = bundle(tmp_path / "codec.zip", [("master.mp4", good)])
    data = bytearray(path.read_bytes())
    struct.pack_into("<H", data, 8, 99)
    struct.pack_into("<H", data, data.index(b"PK\x01\x02") + 10, 99)
    path.write_bytes(data)
    result = recovery.verify_recovery(contract(good), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert result.authority == "NONE"


@pytest.mark.parametrize("member", ["../master.mp4", "..\\master.mp4", "C:/master.mp4", "master.mp4\0hidden", "./master.mp4", "a//master.mp4"])
def test_member_names_have_one_safe_interpretation(member):
    with pytest.raises(ValueError, match="unsafe_container_member"):
        recovery.RecoveryCandidate("c", "local_file", "fixture:c", container_member=member).validate()


@pytest.mark.parametrize("codec", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
@pytest.mark.parametrize("use_zip64", [False, True])
@pytest.mark.parametrize("comment", [b"", b"A" * 65535])
def test_valid_zip_and_zip64_preserve_exact_identity(tmp_path, monkeypatch, codec, use_zip64, comment):
    data = bytes(range(256)) * 4
    path = tmp_path / "valid.zip"
    if use_zip64:
        monkeypatch.setattr(zipfile, "ZIP64_LIMIT", 32)
    with zipfile.ZipFile(path, "w", compression=codec) as archive:
        archive.writestr("master.mp4", data)
        archive.comment = comment
    raw = path.read_bytes()
    assert (b"PK\x06\x06" in raw) == use_zip64
    result = recovery.verify_recovery(contract(data, container_sha=digest(raw)), path)
    assert result.exact
    assert result.observed_bytes == len(data)


def test_directory_bytes_are_bounded_before_zipfile_allocation(tmp_path, monkeypatch):
    path = bundle(tmp_path / "metadata.zip", [("master.mp4", b"x")])
    def forbidden(*args, **kwargs):
        raise AssertionError("constructor read oversized directory")
    monkeypatch.setattr(zipfile, "ZipFile", forbidden)
    with pytest.raises(recovery.RecoveryLimitExceeded, match="zip_directory_bytes_exceeded"):
        recovery.sha256_zip_member(path, "master.mp4", max_directory_bytes=46)


@pytest.mark.parametrize("value", [True, 1.5, float("nan"), float("inf"), 0, -1])
def test_master_expected_bytes_are_typed(value):
    with pytest.raises(ValueError, match="positive integer"):
        recovery.MasterIdentity("master", "a" * 64, value).validate()


def test_corrupted_deflate_is_explicit_invalid_container(tmp_path):
    good = bytes(range(256))
    path = bundle(tmp_path / "broken.zip", [("master.mp4", good)], compression=zipfile.ZIP_DEFLATED)
    raw = bytearray(path.read_bytes())
    data_offset = 30 + len("master.mp4")
    raw[data_offset] = 0xff
    path.write_bytes(raw)
    result = recovery.verify_recovery(contract(good), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert not result.exact


def test_encrypted_member_rejected_without_decompressing(tmp_path, monkeypatch):
    path = bundle(tmp_path / "encrypted.zip", [("master.mp4", b"x")])
    raw = bytearray(path.read_bytes())
    struct.pack_into("<H", raw, 6, 1)
    struct.pack_into("<H", raw, raw.index(b"PK\x01\x02") + 8, 1)
    path.write_bytes(raw)
    def forbidden(*args, **kwargs):
        raise AssertionError("encrypted member was opened")
    monkeypatch.setattr(zipfile.ZipFile, "open", forbidden)
    result = recovery.verify_recovery(contract(b"x"), path)
    assert result.status == recovery.INVALID_CONTAINER


def test_hash_bound_container_mismatch_stops_before_zip_parser(tmp_path, monkeypatch):
    path = bundle(tmp_path / "wrong-container.zip", [("master.mp4", b"x")])
    def forbidden(*args, **kwargs):
        raise AssertionError("mismatched container was parsed")
    monkeypatch.setattr(zipfile, "ZipFile", forbidden)
    result = recovery.verify_recovery(contract(b"x", container_sha="0" * 64), path)
    assert result.status == recovery.CONTAINER_HASH_MISMATCH


@pytest.mark.parametrize("mode", ["symlink", "fifo", "directory"])
def test_non_regular_materialized_candidate_is_not_opened(tmp_path, mode):
    import os
    path = tmp_path / "candidate"
    if mode == "fifo":
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFO is not supported on this host")
        os.mkfifo(path)
    elif mode == "directory":
        path.mkdir()
    else:
        real = tmp_path / "real"
        real.write_bytes(b"x")
        path.symlink_to(real)
    result = recovery.verify_recovery(contract(b"x"), path)
    assert result.status in (recovery.INVALID_CONTAINER, recovery.CANDIDATE_UNAVAILABLE)
    assert not result.exact


def test_streaming_reads_stop_at_limit_plus_one():
    import io
    data = io.BytesIO(b"x" * 100)
    with pytest.raises(recovery.RecoveryLimitExceeded):
        recovery._sha256_stream(data, 7, "container_member")
    assert data.tell() == 8


def test_metadata_reader_fails_before_oversized_read(tmp_path):
    path = tmp_path / "data"
    path.write_bytes(b"x" * 100)
    with path.open("rb") as handle:
        reader = recovery._MetadataReader(handle, 8)
        assert reader.read(3) == b"xxx"
        with pytest.raises(recovery.RecoveryLimitExceeded, match="zip_metadata_read_budget"):
            reader.read(6)
        assert handle.tell() == 3


@pytest.mark.parametrize("mutation", ["truncated", "junk", "split", "wrong-offset", "wrong-count"])
def test_bad_zip_metadata_cannot_gain_identity(tmp_path, mutation):
    data = b"x"
    path = bundle(tmp_path / "bad.zip", [("master.mp4", data)])
    raw = bytearray(path.read_bytes())
    eocd = raw.rfind(b"PK\x05\x06")
    if mutation == "truncated":
        del raw[-10:]
    elif mutation == "junk":
        raw.extend(b"junk")
    elif mutation == "split":
        struct.pack_into("<H", raw, eocd + 4, 1)
    elif mutation == "wrong-offset":
        struct.pack_into("<L", raw, eocd + 16, 1)
    elif mutation == "wrong-count":
        struct.pack_into("<HH", raw, eocd + 8, 0, 0)
    path.write_bytes(raw)
    result = recovery.verify_recovery(contract(data), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert not result.exact


def test_nul_truncated_archive_name_cannot_alias_requested_member(tmp_path):
    good = b"master"
    name = b"master.mp4_hidden"
    path = bundle(tmp_path / "alias.zip", [(name.decode(), good)])
    raw = path.read_bytes().replace(name, b"master.mp4\0hidden")
    path.write_bytes(raw)
    result = recovery.verify_recovery(contract(good), path)
    assert result.status == recovery.INVALID_CONTAINER
    assert "ambiguous_container_member" in result.errors[0]


def test_failure_diagnostics_do_not_echo_untrusted_member_names(tmp_path):
    path = bundle(tmp_path / "missing.zip", [("other", b"x")])
    spec = recovery.RecoveryContract(recovery.MasterIdentity("m", "a" * 64),
        recovery.RecoveryCandidate("c", "local_file", "fixture:c", container_member="private-token-missing"))
    result = recovery.verify_recovery(spec, path)
    assert result.status == recovery.INVALID_CONTAINER
    assert "private-token-missing" not in str(result.errors)
