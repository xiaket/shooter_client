#!/usr/bin/env python
#coding=utf-8
"""
Author:         Xia Kai <xiaket@corp.netease.com/xiaket@gmail.com>
Filename:       shooter_client.py
Date created:   2014-04-30 13:31
Last modified:  2014-05-05 14:27
Modified by:    Xia Kai <xiaket@corp.netease.com/xiaket@gmail.com>

Description:
    For a video file, find it's subtitle from shooter.cn
Changelog:
"""
import hashlib
import os
import sys

import requests


def calculate_checksum(filename):
    """
    calculate the checksum of the file as was used by shooter.cn.
    The whole idea is to sample four parts (start, one third, two thirds,
    end ) of the video file, and calculate their checksum individually.
    """
    sys.stdout.write("Calculating checksum...\n")
    offset = 4096
    fobj = open(filename)
    def md5(position, whence=0):
        m = hashlib.md5()
        fobj.seek(position, whence)
        m.update(fobj.read(offset))
        return m.hexdigest()

    fobj.seek(0, 2)
    filesize = fobj.tell()

    checksum =  ';'.join(
        [md5(offset), md5(filesize/3 * 2), md5(filesize/3), md5(-2*offset, 2)]
    )
    fobj.close()
    return checksum

def get_subtitleinfo(filename):
    """do api request, parse error, return response."""
    sys.stdout.write("Requesting subtitle info...\n")
    response = requests.post(
        "https://www.shooter.cn/api/subapi.php",
        params= {
            'filehash': calculate_checksum(filename),
            'pathinfo': os.path.realpath(filename),
            'format': 'json',
            'lang': "Chn",
        },
    )
    if response.text == u'\xff':
        sys.stderr.write("Subtitle not found.\n")
        sys.exit(1)
    return response

def main(filename):
    if not os.path.isfile(os.path.realpath(filename)):
        sys.stderr.write("File %s not found.\n" % filename)
        sys.exit(1)
    basename = os.path.splitext(filename)[0]

    response = get_subtitleinfo(filename)
    sys.stdout.write("Requesting subtitle file...\n")
    subtitles = set([])
    for count in xrange(len(response.json())):
        if count != 0:
            basename = "%s-alt.%s" % (basename, count)

        for fileinfo in response.json()[count]['Files']:
            url = fileinfo['Link']
            ext = fileinfo['Ext']
            _response = requests.get(url)
            filename = "%s.%s" % (basename, ext)

            if _response.ok and _response.text not in subtitles:
                subtitles.add(_response.text)
                fobj = open(filename, 'w')
                fobj.write(_response.text.encode("UTF8"))
                fobj.close()

if __name__ == '__main__':
    main(sys.argv[1])
