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
    
    If the entry is "faces", create a new entry called "sfaces" consisting
    of the actual names from the contacts.xml file.  i.e.:
    
    ini.faces=rect64(...),e1363a4accda66d5;rect64(...),d80c848976f5bab6
    ini.sfaces="Contact1 Name","Contact 2 Name"
    
    If the entry is "crop", create a new entry called "cropxy" consisting
    of the x,y coordinates of the rectangle (upper left xy, lower right xy,
    0.0 to 1.0 normalized.  i.e.: 
    
    ini.crop=rect64(5bf05d4f9bcfad1)
    ini.cropxy=0.022446,0.022766,0.975540,0.979767
    
    '''
    
    
    def __init__(self,iniFile,contacts):
        '''
        Read a .picasa.ini file into a dictionary.  The full path to this
        .picasa.ini file is stored in self.filePath so it can be found again.
        contacts is a picasa3meta.contacts.Contacts class object
        
        '''
        
        self.filePath = os.path.dirname(iniFile)

        self.names = []     # a list of files names in this .picasa.ini
        self.contents = {}  # a dictionary, indexed by names[x], 
                            # containing a list of string objects
        
        inIni = open(iniFile,"r")
        i=0
        
        for line in inIni:
            line = line.rstrip('\n\r')
            try:
                # check if line is "^[<image>]$" (start of a file entry)
                m = re.search('(?<=\[)[^\]]+',line)
                image = m.group(0)
                
                # Yes, create a new entry in names/contents
                
                self.names.append(image)
                self.contents[self.names[i]] = []
                i += 1
            except:
                # No, append the line to the current contents[names[x]] dict
                if len(self.names) == 0:
                    raise IniStructError(
                        "unexpected lines in %s before a file designator"%
                        iniFile)
                else:  
                    self.contents[self.names[i-1]].append(line.replace('=',':',1))
                    (key,sep,val) = line.partition('=')
                    if key == "faces":
                        sfaces = "sfaces:"
                        for people in val.split(';'):
                            if sfaces != "sfaces:":
                                sfaces += ","
                            person = people.split(',')
                            sfaces += '"'+contacts.getContact(person[1])+'"'
                        self.contents[self.names[i-1]].append(sfaces)
                    elif key == "crop":
                        m1 = re.search('(?<=rect64\()[^\)]+',val)
                        crop64 = long(m1.group(0),16)
                        mx = float(int(0xffff))
                        x1 = float((crop64&0xffff000000000000)>>48)/mx
                        y1 = float((crop64&0x0000ffff00000000)>>32)/mx
                        x2 = float((crop64&0x00000000ffff0000)>>16)/mx
                        y2 = float( crop64&0x000000000000ffff)/mx
                        self.contents[self.names[i-1]].append(
                            "cropxy:%f,%f,%f,%f"%(x1,y1,x2,y2))                                     
        inIni.close()
        
    def getFileEntry(self,image):
        '''
        Return a list object of the entries for this image from the
        contents dictionary
        
        '''
        
        if self.contents.has_key(image):
            return self.contents[image]
        else:
            return []
    
    def iniEntry(self,index):
        '''
        Diagnostic function - returns an entry by index
        
        '''
        
        return  [ self.names[index], self.filePath, 
                 self.contents[self.names[index]] ]
    
    def iniDump(self):
        '''
        Diagnostic function
        
        '''
        
        for i in range(len(self.names)):
            ret = [ os.path.join(self.filePath,self.names[i]+".ini") ] + \
                self.contents[self.names[i]] 
            for j in range(len(ret)):
                yield ret[j]
            
            
