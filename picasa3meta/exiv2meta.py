'''
This file is part of picasa3meta.

picasa3meta is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

picasa3meta is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with picasa3meta.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2012 Wayne Vosberg <wayne.vosberg@mindtunnel.com>
'''
import pyexiv2


def EXIV2Meta(img):
    '''

    Return a list of tuples of all the EXIF, IPTC and XMP metadata in a file.

    Usage:
        from picasa3meta import exiv2meta

        metaData = exiv2meta.EXIV2Meta("/path/to/file.jpg")

        for key,value in metaData:
            print "%s : %s"%(key,value)

    Exif keys will return the human_value if possible, otherwise the raw_value.

    Iptc keys will return the raw_value first, if that fails, just value

    Xmp keys may be dict objects.  If it is a dict, return a comma separated
    list of the values.  Otherwise, try the raw_value first, then just value.

    '''

    try:
        metadata = pyexiv2.ImageMetadata(img)
        metadata.read()
    except:
        return zip(['error'], ['%s is not an image' % img])
    else:
        ret = []

        for K in metadata.exif_keys:
            try:
                ret.append(metadata[K].human_value)
            except:
                ret.append(metadata[K].raw_value)

        for K in metadata.iptc_keys:
            try:
                ret.append(metadata[K].raw_value[0])
            except:
                ret.append(metadata[K].value[0])

        for K in metadata.xmp_keys:
            if type(metadata[K].raw_value) == dict:
                # if the xmp key is a dict, return it as a comma separated list
                nret = ""
                for KK in metadata[K].raw_value:
                    if len(nret) > 1:
                        nret = nret + ","
                    nret = nret + metadata[K].raw_value[KK]
                ret.append(nret)
            else:
                try:
                    ret.append(metadata[K].raw_value)
                except:
                    ret.append(metadata[K].value)

        # zip the keys and values into a list of tuples and return it
        return zip(metadata.exif_keys + metadata.iptc_keys + metadata.xmp_keys,
                    ret)
