#!/usr/bin/python

import ctypes
import getpass
import subprocess
import os
import pwd


def call(*args, **kwargs):
    print args[0]#; return 0
    return subprocess.check_call(*args, **kwargs)


def keyctl_clear():
    libkeyutils = ctypes.cdll.LoadLibrary("libkeyutils.so.1")
    KEY_SPEC_USER_KEYRING = -4 # from keyutils.h
    keyring = libkeyutils.keyctl_get_keyring_ID(KEY_SPEC_USER_KEYRING, 0)
    libkeyutils.keyctl_clear(keyring)


def ecryptfs_insert_wrapped_passphrase_into_keyring(filepath, passphase):
    libecryptfs = ctypes.cdll.LoadLibrary("libecryptfs.so.0")

    ECRYPTFS_SIG_SIZE_HEX = 16
    auth_tok_sig_hex = ctypes.create_string_buffer("\0" * ECRYPTFS_SIG_SIZE_HEX)

    ECRYPTFS_DEFAULT_SALT_HEX = ["00", "11", "22", "33", "44", "55", "66", "77"]
    salt = []
    for a, b in ECRYPTFS_DEFAULT_SALT_HEX:
        salt.append(chr(int("%s%s" % (a, b), 16)))
    salt = "".join(salt)

    rc = libecryptfs.ecryptfs_insert_wrapped_passphrase_into_keyring(
        auth_tok_sig_hex, filepath, passphase, salt)
    if rc != 0:
        raise RuntimeError("ecryptfs_insert_wrapped_passphrase_into_keyring: %s" % rc)
    return auth_tok_sig_hex.value


if __name__ == "__main__":
    passphase = getpass.getpass("Wrapping passphase: ")
    pw = pwd.getpwuid(os.getuid())
    ecryptfs_insert_wrapped_passphrase_into_keyring(
        os.path.join(pw.pw_dir, ".ecryptfs", "wrapped-passphrase"), passphase)
    if os.path.join(pw.pw_dir, "Private") in open("/proc/mounts").read():
        call(["ecryptfs-umount-private"])
    else:
        call(["ecryptfs-mount-private"])
    keyctl_clear()

