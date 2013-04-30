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
import os
import re


class IniError(Exception):
    pass

class    IniStructError(IniError):
    pass


class IniInfo(object):
    '''

    Read a .picasa.ini file and save as a Python dictionary:
    { filename:[ent1, ent2, ent3, ...], filename:[en1, ent2, ent3, ...], ... }

    Usage:

        from picasa3meta import iniinfo

        myIni = iniinfo.IniInfo("/path/to/.picasa.ini" [, myContacts] )

        print ".picasa.ini file in %s"%myIni.filePaht

        for imageFile in myIni.names:
            print "    image: %s"%imageFile
            for iniEntry in myIni.getFileEntry(imageFile):
                print "        %s"%iniEntry


        --OR--

        for imageFile, iniEntrys in myIni.contents.iteritems():
            print "    image: %s"%imageFile
            for iniEntry in iniEntrys:
                print "        %s"%iniEntry



    Picasa3 creates a .picasa.ini file in each directory with the format:

        [Picasa]
        name=Picasa Album Name
        date=40788.407998
        P2category=Folders on Disk
        [IMG_0001.JPG]
        backuphash=11776
        caption=what is this
        [IMG_0002.JPG]
        backuphash=11886
        caption=another photo
        .
        .
        .

    This would return:

        { 'IMG_0001.JPG':['backuphash:11776', 'caption:what is this'],
            'IMG_0002.JPG':['backuphash:11886', 'caption:another photo'] }

    If you specify a 'contacts' object and the entry is "faces", also create
    a new entry called "sfaces" consisting of the actual names from the
    contacts.xml file.  i.e.:

        faces:rect64(...),e1363a4accda66d5;rect64(...),d80c848976f5bab6
        sfaces:"Contact1 Name","Contact 2 Name"

    If the entry is "crop", create a new entry called "cropxy" consisting
    of the x,y coordinates of the rectangle (upper left xy, lower right xy,
    0.0 to 1.0 normalized.  i.e.:

        crop=rect64(5bf05d4f9bcfad1)
        cropxy=0.022446,0.022766,0.975540,0.979767

    '''


    def __init__(self, iniFile, contacts=None):
        '''

        Read a .picasa.ini file into a dict.

        The full path to this .picasa.ini file is stored in self.filePath
        so if you have multiple IniInfo objects you can keep them sorted.

        A list of filename in this .picasa.ini is save in self.names[] for
        convenience.

        The contents of this .picasa.ini are stored as self.contents{}

        contacts, if specified, must be a picasa3meta.contacts.Contacts object.

        '''

        self.filePath = os.path.dirname(iniFile)

        self.names = []  # a list of files names in this .picasa.ini
        self.contents = {}  # a dict, indexed by names[x],
                            # containing a list of string objects

        inIni = open(iniFile, "r")
        i = 0

        for line in inIni:
            line = line.rstrip('\n\r')
            try:
                # check if line is "^[<image>]$" (start of a file entry)
                m = re.search('(?<=\[)[^\]]+', line)
                image = m.group(0)

                # Yes? Create a new entry in names/contents
                self.names.append(image)
                self.contents[self.names[i]] = []
                i += 1

            except:
                # No? Append the line to the current contents[names[x]] dict
                if len(self.names) == 0:
                    raise IniStructError(
                        "unexpected lines in %s before a file designator"\
                        % iniFile)
                else:
                    self.contents[self.names[i - 1]].\
                        append(line.replace('=', ':', 1))
                    (key, sep, val) = line.partition('=')
                    if key == "faces" and contacts != None:
                        sfaces = "sfaces:"
                        for people in val.split(';'):
                            if sfaces != "sfaces:":
                                sfaces += ","
                            person = people.split(',')
                            # people has the form 'rect(),id', so split that
                            # on the ',' and the id is person[1]
                            sfaces += '"' + contacts.getContact(person[1]) + '"'
                        self.contents[self.names[i - 1]].append(sfaces)
                    elif key == "crop":
                        m1 = re.search('(?<=rect64\()[^\)]+', val)
                        crop64 = long(m1.group(0), 16)
                        mx = float(int(0xffff))
                        x1 = float((crop64 & 0xffff000000000000) >> 48) / mx
                        y1 = float((crop64 & 0x0000ffff00000000) >> 32) / mx
                        x2 = float((crop64 & 0x00000000ffff0000) >> 16) / mx
                        y2 = float(crop64 & 0x000000000000ffff) / mx
                        self.contents[self.names[i - 1]].append(
                            "cropxy:%f,%f,%f,%f" % (x1, y1, x2, y2))
        inIni.close()



    def getFileEntry(self, image):
        '''Return a list of strings of the ini file entries for this image.'''

        if self.contents.has_key(image):
            return self.contents[image]
        else:
            return []



    def iniEntry(self, index):
        ''' Diagnostic function - returns an entry by index '''

        return  [ self.names[index], self.filePath,
                 self.contents[self.names[index]] ]



    def iniDump(self):
        ''' Diagnostic function '''

        for i in range(len(self.names)):
            ret = [ os.path.join(self.filePath, self.names[i] + ".ini") ] + \
                self.contents[self.names[i]]
            for j in range(len(ret)):
                yield ret[j]
