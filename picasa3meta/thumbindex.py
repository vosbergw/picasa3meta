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

import array
import os


class ThumbError(Exception):
    pass

class    MagicError(ThumbError):
    pass

class   ThumbIndexError(ThumbError):
    pass

class ThumbIndex(object):
    '''
    Read the Picasa3 thumbindex.db file, verify the magic byte and save
    all entries into the name[] and pathIndex[] lists

    If a files has been removed from Picasa3 that thumbindex entry will not be
    reused.  Requesting that entry will return a null file/path name.

    Requesting the index of a file that does not exist (or has been deleted)
    will return -1 (0xffffffff)

    usage:
        from picasa3meta import thumbindex

        db = thumbindex.ThumbIndex("/path/to/Picasa3/db3/thumbindex.db")

        # find index of image.jpg data in Picasa3 imagedata_xxx.pmp files
        pmpIndex = db.indexOfFile("/full/path/to/Picasa3/image.jpg")

        # find the basename of the image file at pmpIndex
        imageName = db.imageName(pmpIndex)

        # find the path of the image file at pmpIndex
        imagePath = db.imagePath(pmpIndex)

        # return the full path/file name of the image file at pmpIndex
        imageFullName = db.imageFullName(pmpIndex)

        # assuming pmp is a pmpinfo object for the imagedata table, retrieve
        # the database entry for a file
        index = db.indexOfFile("/full/path/to/file.jpg")
        for col, val in pmp.getEntry(index):
            print "column %s is %s"%(col,val)

    The thumbindex.db file format is:

        |magic byte |# entries    |null terminated path/file |
        |40 46 66 66|xx xx xx xx|ascii ................. 00|

        |26 bytes unknown                                  |
        |xx xx xx xx xx xx ............................. xx|

        |index      |repeat from 'null terminated path/file' above ...
        |xx xx xx xx|

        The index is the index into the array for the entry of the parent
        directory of the file, or 0xffffffff if this entry is a directory.

        If the file path/filename length is 0 then this file or path has been
        deleted.    Just set the index to 0xffffffff so that it is ignored.

    '''

    def __init__(self, thumbindex):
        '''

        Open file "thumbindex", verify the magic byte (0x40466666), and then
        read all entries into name[], pathIndex[] arrays.

        '''

        self.header = array.array('I')
        self.entries = 0
        self.name = []
        self.unknown26 = []
        self.orgPathIndex = array.array('I')
        self.pathIndex = array.array('I')

        self.facesArray = {}

        self.inFile = open(thumbindex, "rb")
        self.header.fromfile(self.inFile, 2)

        if self.header[0] != 0x40466666:
            raise MagicError("magic bytes %#x != 0x40466666" % self.header[0])

        self.entries = self.header[1]  # number of entries I expect to find

        self.index = 0
        self.name.append("")

        while True:
            # thumb entry begins with a null terminated string which gives
            # the filename or pathname
            self.b = self.inFile.read(1)
            if len(self.b) == 0:  # EOF
                if self.index != self.entries:
                    raise ThumbIndexError(
                        "expected %d entries but only found %d" %
                        (self.entries, self.index))
                else:
                    return

            # file/path name will terminate with a null or 0xff char
            # 0xff? not sure where this came from but I'm going to leave it in.
            if self.b == chr(0xff) or self.b == chr(0):
                # self.a = self.inFile.read(26)   # toss the next 26 bytes
                self.unknown26.append(array.array('B'))
                self.unknown26[self.index].fromfile(self.inFile, 26)
                # the next int is the index into the names array of the
                # path to this file or 0xffffffff if this is a directory
                self.pathIndex.fromfile(self.inFile, 1)
                self.orgPathIndex.append(self.pathIndex[self.index])

                if len(self.name[self.index]) == 0:
                    # if there was no file name read then this file or
                    # directory has been deleted.  Just set the path to
                    # 0xffffffffff so we ignore it
                    self.pathIndex[self.index] = 0xffffffff
                    # now populate the facesArray dictionary --
                    # facesArray = { image_index:[ face1_index,
                    #                face2_index, ...], ... }
                    #
                    if self.orgPathIndex[self.index] != 0xffffffff:
                        if self.facesArray.has_key(
                                self.orgPathIndex[self.index]):
                            self.facesArray[self.orgPathIndex[self.index]].\
                                append(self.index)
                        else:
                            self.facesArray[self.orgPathIndex[self.index]] = []
                            self.facesArray[self.orgPathIndex[self.index]].\
                                append(self.index)

                self.index += 1
                self.name.append("")
            else:
                self.name[self.index] += self.b  # valid file/path name char


    def indexOfFile(self, findMe):
        '''

        Find the index into the imagedata_xxx.pmp files for an image file.
        Returns -1 if the image file is not found.

        '''

        self.findPath = os.path.dirname(findMe) + "/"
        self.findName = os.path.basename(findMe)

        for i in range(self.entries):
            if self.pathIndex[i] != 0xffffff:
                if self.name[i] == self.findName:
                    if self.name[self.pathIndex[i]] == self.findPath:
                        return i

        return -1

    def imagePath(self, what):
        '''

        Find the path of the file at entry 'what'.

        If entry 'what' is a directory itself or is an image that has been
        removed, just return an empty string.  An exception will be thrown
        if you ask for an entry > number of entries in thumbindex.db

        '''

        if self.pathIndex[what] == 0xffffffff:
            return ""
        else:
            return self.name[self.pathIndex[what]]

    def imageName(self, what):
        '''

        Find the basename of the file at entry 'what'.

        An exception will be thrown if you ask for an entry > number of entries
        in thumbindex.db (self.entries)

        '''

        return self.name[what]

    def imageFullName(self, what):
        '''
        Find the full path name of the file/directory at entry 'what'.

        An exception will be thrown if you ask for an entry > number of entries
        in thumbindex.db (self.entries)

        '''

        return os.path.join(self.imagePath(what), self.imageName(what))



    def getFaces(self, what):
        '''return a list of the faces in 'what' '''

        if self.facesArray.has_key(what):
            return self.facesArray[what]
        else:
            return None

    def hasFaces(selfself, what):
        '''return true if there is an entry in facesArray for this entry'''

        if self.facesArray.has_key(what):
            return True
        else:
            return False


    def dumpFaces(self, what):
        '''dump the faces array for image 'what' '''

        if self.facesArray.has_key(what):
            return self.facesArray[what]
        else:
            return None



    def dump(self, what):
        '''diagnostic dump of the entry at 'what' '''

        print '\n[%06d / %#08x] ' % (what, what),
        if self.orgPathIndex[what] == 0xffffffff:  # directory
            print 'd[%s] p[%#0x]' % (self.name[what], self.orgPathIndex[what])
        else:
            if len(self.name[what]) > 0 and self.pathIndex[what] == 0xffffffff:
                print 'r[%s] p[%06d]'\
                    % (self.name[what], self.orgPathIndex[what])
            elif len(self.name[what]) > 0 and \
                    self.pathIndex[what] != 0xffffffff:
                print 'f[%s] p[%06d : %s]' % (self.name[what],
                    self.pathIndex[what], self.name[self.pathIndex[what]])
            elif len(self.name[what]) == 0 and self.orgPathIndex != 0xffffffff:
                print '?[%s] p[%06d : %s]' % (self.name[what],
                    self.orgPathIndex[what], self.name[self.orgPathIndex[what]])
            else:
                print '-[%s] p[%06d]' % (self.name[what],
                    self.orgPathIndex[what])
        for i in range(26):
            print '%02x ' % self.unknown26[what][i],
        print ''
