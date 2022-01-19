#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : WindowsBuildFromISO.py
# Author             : Podalirius (@podalirius_)
# Date created       : 19 Jan 2022

import argparse
import os
import sys
import tempfile
import xml.etree.ElementTree as ET


def check_windows_version(isofile, verbose=False):
    # Mount iso read-only
    oldpwd = os.getcwd()
    iso_mount_dir = tempfile.TemporaryDirectory()
    work_dir = tempfile.TemporaryDirectory()
    if verbose:
        print("   [>] Work dir is %s/" % work_dir.name)
    if verbose:
        print("   [>] Mounting ISO to %s/" % iso_mount_dir.name)
        print("     | mount -o ro '%s' %s/ 2>&1" % (isofile, iso_mount_dir.name))
        os.system("mount -o ro '%s' %s/ 2>&1" % (isofile, iso_mount_dir.name))
    else:
        os.popen("mount -o ro '%s' %s/ 2>&1" % (isofile, iso_mount_dir.name)).read()
    os.chdir(iso_mount_dir.name)

    # Parse files in the ISO to get the Windows build
    if verbose:
        print("   [>] Parsing Windows build number ...")
    os.chdir(work_dir.name)
    if verbose:
        print("   [>] Extracting boot.wim '[1].xml' file ...")
        os.system("7z e '%s/sources/boot.wim' '[1].xml' 2>&1" % iso_mount_dir.name)
    else:
        os.popen("7z e '%s/sources/boot.wim' '[1].xml' 2>&1" % iso_mount_dir.name).read()
    if verbose:
        print("   [>] Parsing boot.wim '[1].xml' file ...")
    tree = ET.parse('[1].xml')
    # for image in tree.findall('IMAGE')[0]:
    image = tree.findall('IMAGE')[0]
    windows = image.find('WINDOWS')
    # Versions
    versions = {c.tag.lower(): c.text for c in list(windows.find('VERSION'))}
    version_string = "%s.%s.%s.%s" % (versions['major'], versions['minor'], versions['build'], versions['spbuild'])
    # Languages
    languages = [l.text for l in windows.findall('LANGUAGES/LANGUAGE')]
    languages_string = ("multi" if len(languages) > 1 else languages[0].lower())

    os.chdir(oldpwd)
    # Unmount ISO and remove temporary directory
    if options.verbose:
        print("[>] Unmounting ISO from %s ..." % iso_mount_dir.name)
        os.system("umount %s 2>&1" % iso_mount_dir.name)
    else:
        os.popen("umount %s 2>&1" % iso_mount_dir.name).read()
    work_dir.cleanup()
    iso_mount_dir.cleanup()
    return (versions, version_string, languages_string)


def archive_iso(archive_dir, iso, versions, version_string, languages_string, verbose=False):
    basedir = "%s/Windows %s.%s/%s - Windows %s.%s/%s/" % (archive_dir, versions['major'], versions['minor'], version_string, versions['major'], versions['minor'], languages_string)
    isoname = '.'.join(os.path.basename(iso).split('.')[:-1])
    isoname = "%s.%s.%s.%s.iso" % (version_string, isoname, versions['branch'], languages_string)
    if not os.path.exists(basedir):
        os.makedirs(basedir, exist_ok=True)
    if verbose:
        print("[>] Archiving to %s/%s" % (basedir, isoname))
    os.rename(iso, "%s/%s" % (basedir, isoname))


def parseArgs():
    parser = argparse.ArgumentParser(description="Extract Windows Build number from ISO files. v1.1")
    group_iso_source = parser.add_mutually_exclusive_group(required=True)
    group_iso_source.add_argument("-i", "--iso", default=None, help='Path to iso file.')
    group_iso_source.add_argument("-d", "--iso-dir", default=None, help='Directory containing multiple ISOs to parse.')
    parser.add_argument("-a", "--archive-dir", default=None, help='Archive dir. (default: False)')
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help='Verbose mode. (default: False)')
    return parser.parse_args()


if __name__ == '__main__':
    options = parseArgs()

    if options.iso is not None:
        if not os.path.isfile(options.iso):
            print("[!] Cannot access ISO file. Wrong path or bad permissions maybe ?")
            sys.exit(-1)
        versions, version_string, languages_string = check_windows_version(options.iso, verbose=options.verbose)
        print("==> Windows %s.%s (build:%s.%s) (lang:%s)" % (versions['major'], versions['minor'], versions['build'], versions['spbuild'], languages_string))
        if options.archive_dir is not None:
            archive_iso(options.archive_dir, options.iso, versions, version_string, languages_string, verbose=options.verbose)
    elif options.iso_dir is not None:
        if not os.path.isdir(options.iso_dir):
            print("[!] Cannot access ISO directory. Wrong path or bad permissions maybe ?")
            sys.exit(-1)
        iso_files = []
        if options.verbose:
            print("[debug] Searching for iso files ...")
        for root, dirs, files in os.walk(options.iso_dir):
            for filename in files:
                if filename.lower().endswith(".iso"):
                    name = os.path.join(root, filename)
                    iso_files.append(name)
        for iso in iso_files:
            print("[iso] %s " % iso)
            versions, version_string, languages_string = check_windows_version(iso, verbose=options.verbose)
            print("    |==> Windows %s.%s (build:%s.%s) (lang:%s)" % (versions['major'], versions['minor'], versions['build'], versions['spbuild'], languages_string))
            if options.archive_dir is not None:
                archive_iso(options.archive_dir, iso, versions, version_string, languages_string, verbose=options.verbose)

