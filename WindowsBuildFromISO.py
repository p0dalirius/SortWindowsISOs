#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : WindowsBuildFromISO.py
# Author             : Podalirius (@podalirius_)
# Date created       : 19 Jan 2022

import argparse
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET


def check_windows_version(isofile, verbose=False):
    versions, version_string, display_name, languages_string = None,None,None,None
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
    os.chdir(work_dir.name)
    try:
        if os.path.isfile(iso_mount_dir.name + "/sources/install.wim"):
            if verbose:
                print("   [>] Parsing Windows build number ...")
            if verbose:
                print("   [>] Extracting install.wim '[1].xml' file ...")
                os.system("7z e '%s/sources/install.wim' '[1].xml' -aoa 2>&1" % iso_mount_dir.name)
            else:
                os.popen("7z e '%s/sources/install.wim' '[1].xml' -aoa 2>&1" % iso_mount_dir.name).read()
            if verbose:
                print("   [>] Parsing install.wim '[1].xml' file ...")
            tree = ET.parse('[1].xml')
            image = tree.findall('IMAGE')[0]
            windows = image.find('WINDOWS')
            # Versions
            versions = {c.tag.lower(): c.text for c in list(windows.find('VERSION'))}
            version_string = "%s.%s.%s.%s" % (versions['major'], versions['minor'], versions['build'], versions['spbuild'])
            # Languages
            languages = [l.text for l in windows.findall('LANGUAGES/LANGUAGE')]
            languages_string = ("multi" if len(languages) > 1 else languages[0].lower())
            # Display name
            display_name = image.find('DISPLAYNAME').text.strip()
            if "Evaluation" in display_name:
                display_name = display_name.replace("Evaluation", "").strip()

        elif os.path.isfile(iso_mount_dir.name + "/sources/boot.wim"):
            if verbose:
                print("   [>] Parsing Windows build number ...")
            if verbose:
                print("   [>] Extracting boot.wim '[1].xml' file ...")
                os.system("7z e '%s/sources/boot.wim' '[1].xml' -aoa 2>&1" % iso_mount_dir.name)
            else:
                os.popen("7z e '%s/sources/boot.wim' '[1].xml' -aoa 2>&1" % iso_mount_dir.name).read()
            if verbose:
                print("   [>] Parsing boot.wim '[1].xml' file ...")
            tree = ET.parse('[1].xml')
            image = tree.findall('IMAGE')[0]
            windows = image.find('WINDOWS')
            # Versions
            versions = {c.tag.lower(): c.text for c in list(windows.find('VERSION'))}
            version_string = "%s.%s.%s.%s" % (versions['major'], versions['minor'], versions['build'], versions['spbuild'])
            # Languages
            languages = [l.text for l in windows.findall('LANGUAGES/LANGUAGE')]
            languages_string = ("multi" if len(languages) > 1 else languages[0].lower())
            # Display name
            display_name = image.find('DISPLAYNAME')
            if display_name is not None:
                display_name = display_name.text.strip()
            else:
                if versions['minor'] != "0":
                    display_name = "Windows %s.%s" % (versions['major'], versions['minor'])
                else:
                    display_name = "Windows %s" % (versions['major'])
    except Exception as e:
        print("   [\x1b[91merror\x1b0m] %s" % e)

    os.chdir(oldpwd)
    # Unmount ISO and remove temporary directory
    if options.verbose:
        print("[>] Unmounting ISO from %s ..." % iso_mount_dir.name)
        os.system("umount %s 2>&1" % iso_mount_dir.name)
    else:
        os.popen("umount %s 2>&1" % iso_mount_dir.name).read()
    work_dir.cleanup()
    iso_mount_dir.cleanup()
    return (versions, version_string, display_name, languages_string)


def archive_iso(archive_dir, iso, versions, version_string, display_name, languages_string, verbose=False):
    os_type = ""
    display_name = display_name.strip()
    m = re.match('^(Windows [0-9]+(\.[0-9]+)?)', display_name)
    if m is not None:
        os_type = m.group(0)
    m = re.match('^(Windows Server [0-9]+)', display_name)
    if m is not None:
        os_type = m.group(0)
    if os_type == "":
        os_type = display_name

    basedir = "%s/%s/%s - %s/%s/" % (archive_dir, os_type, version_string, display_name, languages_string)
    # basedir = basedir.replace(' ', '_')
    isoname = display_name.replace(' ', '_')
    if "branch" in versions.keys():
        isoname = "%s.%s.%s.%s.iso" % (version_string, isoname, versions['branch'], languages_string)
    else:
        isoname = "%s.%s.%s.iso" % (version_string, isoname, languages_string)
    if not os.path.exists(basedir):
        os.makedirs(basedir, exist_ok=True)
    if verbose:
        print("   [>] Archiving to %s/%s" % (basedir, isoname))
    os.rename(iso, "%s/%s" % (basedir, isoname))


def print_windows_version(versions, display_name, languages_string, no_colors=False):
    _os, _build, _lang, _branch = "", "", "", ""
    # Windows version
    if no_colors:
        _os = "%s" % display_name
    else:
        _os = "\x1b[92m%s\x1b[0m" % display_name
    # Build
    if no_colors:
        _build = "(build:%s.%s)" % (versions['build'], versions['spbuild'])
    else:
        _build = "(\x1b[94mbuild\x1b[0m:\x1b[96m%s.%s\x1b[0m)" % (versions['build'], versions['spbuild'])
    # Branch
    if "branch" in versions.keys():
        if no_colors:
            _branch = "(branch:%s)" % (versions['branch'])
        else:
            _branch = "(\x1b[94mbranch\x1b[0m:\x1b[96m%s\x1b[0m)" % (versions['branch'])
    # Languages
    if no_colors:
        _lang = "(lang:%s)" % languages_string
    else:
        _lang = "(\x1b[94mlang\x1b[0m:\x1b[96m%s\x1b[0m)" % languages_string
    print("   [+] %s %s %s %s" % (_os, _build, _branch, _lang))


def parseArgs():
    parser = argparse.ArgumentParser(description="Extract Windows Build number from ISO files. v1.1")
    group_iso_source = parser.add_mutually_exclusive_group(required=True)
    group_iso_source.add_argument("-i", "--iso", default=None, help='Path to iso file.')
    group_iso_source.add_argument("-d", "--iso-dir", default=None, help='Directory containing multiple ISOs to parse.')
    parser.add_argument("-a", "--archive-dir", default=None, help='Archive dir. (default: False)')
    parser.add_argument("-v", "--verbose", default=False, action="store_true", help='Verbose mode. (default: False)')
    parser.add_argument("--no-colors", default=False, action="store_true", help='No colors mode. (default: False)')
    return parser.parse_args()


if __name__ == '__main__':
    options = parseArgs()

    if options.iso is not None:
        if not os.path.isfile(options.iso):
            print("[!] Cannot access ISO file. Wrong path or bad permissions maybe ?")
            sys.exit(-1)
        print("[iso] %s " % options.iso)
        try:
            versions, version_string, display_name, languages_string = check_windows_version(options.iso, verbose=options.verbose)
            print_windows_version(versions, display_name, languages_string, no_colors=options.no_colors)
            if options.archive_dir is not None:
                archive_iso(options.archive_dir, options.iso, versions, version_string, display_name, languages_string, verbose=options.verbose)
        except Exception as e:
            print("   [\x1b[91merror\x1b0m] %s" % e)
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
            try:
                versions, version_string, display_name, languages_string = check_windows_version(iso, verbose=options.verbose)
                print_windows_version(versions, display_name, languages_string, no_colors=options.no_colors)
                if options.archive_dir is not None:
                    archive_iso(options.archive_dir, iso, versions, version_string, display_name, languages_string, verbose=options.verbose)
            except Exception as e:
                print("   [\x1b[91merror\x1b0m] %s" % e)

