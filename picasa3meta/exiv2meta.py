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
along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2012 Wayne Vosberg <wayne.vosberg@mindtunnel.com>
'''
import pyexiv2


def EXIV2Meta(img):
    '''
    Return a list of all the EXIF, IPTC and XMP metadata in the file 'iimg'
    
    '''
    
    try:
        metadata = pyexiv2.ImageMetadata(img)
        metadata.read()
    except:
        return zip( ['error'],['%s is not an image'%img])
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
                nret=""
                for KK in metadata[K].raw_value:
                    if len(nret) > 1:
                        nret = nret+","
                    nret = nret+metadata[K].raw_value[KK]
                ret.append(nret)
            else:
                try:
                    ret.append(metadata[K].raw_value)
                except:
                    ret.append(metadata[K].value)
         
        return zip(
            metadata.exif_keys+metadata.iptc_keys+metadata.xmp_keys, ret )
    