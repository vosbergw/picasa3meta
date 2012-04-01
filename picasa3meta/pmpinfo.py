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
import os
import fnmatch
import array
import math
import datetime
import re
import struct

def locatedir(pattern,start):
    '''Search for a directory'''
    for path, dirs, files in os.walk(os.path.abspath(start)):
        for dir in fnmatch.filter(dirs, pattern):
            yield os.path.join(path, dir)

def locate(pattern,start):
    '''Search for a file'''
    for path, dirs, files in os.walk(os.path.abspath(start)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


class PmpError(Exception):
    pass

class    PmpMagicError(PmpError):
    pass


class PmpSizeError(PmpError):
    pass

class    PmpTypeError(PmpError):
    pass

class PmpInfo(object):
    '''
    Read an entire picasa pmp database table.  This table resides in multiple
    files in Picasa3/db3 with names: <table_name>_<column_name>.pmp
    
    usage:
    
    from picasa3meta import pmpinfo
    
    pmp = pmpinfo.PmpInfo("imagedata","/path/to/Picasa3/db3")
    
    for K,V in pmp.colSizes():
        print "column %s has %d entries"%(K,V)
        
    '''
        
    def __init__(self,dbpath, dbtable):
        '''
        Read the entire table.  Class variables are:
        
        tableName: 
            i.e. 'imagedata'
        columns: 
            list of columns, i.e. [ 'caption', 'date', 'filter', ... ]
        data:
            dictionary of all data, i.e. 
            { 'caption':[ 'cap 0', 'cap 1', ... ], 
              'date': [ d0, d1, ... ], ... }
        magic: 
            list of magic byte from each file.  shoule be 
            [ 0x3fcccccd, 0x3fcccccd, ... ]
        type1: 
            list of type of data in this column: [ 0, 3, 0, 1, ...]
        c1:    
            list of static shorts in the header: [ 0x1332, 0x1332, ...]
        c2:    
            list of static longs in the header: 
            [ 0x02, 0x02, 0x02, ...] (see doHeader())
        type2: 
            list of type of data in this column.  must =type1
        size:  
            list of length of each column: [ 2000, 3000, 1295, ... ]
            
        '''
        
        self.tableName = dbtable
        self.columns = []
        self.data = {}
        
        self.magic = []
        self.type1 = []
        self.c1 = []
        self.c2 = []
        self.type2 = []
        self.c4 = []
        self.size = []
        
        i=0
                   
        for dbFile in locate(self.tableName+"_*.pmp",dbpath):
            count = 0
            self.columns.append("")
            
            # find the column name in this file (drop the .pmp and
            # remove everything before (and including) the first '_'
            m = re.search('(?<=_)[^$]+',os.path.splitext(dbFile)[0]) 
            self.columns[i] = m.group(0)
                
            pmp = open(dbFile,"rb")
        
            self.doHeader(pmp,i)
        
            if self.type1[i] == 0x0: # null terminated strings
                count = self.doStrings(pmp,self.columns[i])
            elif self.type1[i] == 0x1:  # unsigned integers (4 bytes)
                count = self.doUint(pmp,self.columns[i],self.size[i])
            elif self.type1[i] == 0x2:  # double float (8 bytes)
                count = self.doFloat(pmp,self.columns[i],self.size[i])
            elif self.type1[i] == 0x3:  # unsigned char (1 byte)
                count = self.doByte(pmp,self.columns[i],self.size[i])
            elif self.type1[i] == 0x4:  # unsigned long (8 bytes)
                count = self.doUlong(pmp,self.columns[i],self.size[i])
            elif self.type1[i] == 0x5:  # unsigned short (2 bytes)
                count = self.doUshort(pmp,self.columns[i],self.size[i])
            elif self.type1[i] == 0x6:  # null terminated strings
                count = self.doStrings(pmp,self.columns[i])
            elif self.type1[i] == 0x7:  # unsigned integers (4 bytes)
                count = self.doUint(pmp,self.columns[i],self.size[i])
            else:
                raise PmpTypeError("unknown type: %d"%self.type1[i])
            
            if count != self.size[i]:
                raise PmpSizeError(
                    "expected %d entries in %s/%s but read %d"%
                    (self.size[i],self.tableName,self.columns[i],count))
            
            i += 1
            pmp.close()
    
    
    def doHeader(self,pmp,i):    
        '''
        read and verify the pmp header:
        
        magic------|type1|c1---|c2---------|type2|size---------|
        3f cc cc cd T1 T1 13 32 00 00 00 02 T2 T2 SS SS SS SS SS
        
        '''
        
        self.magic.append(struct.unpack("I",pmp.read(4))[0])
        self.type1.append(struct.unpack("H",pmp.read(2))[0])
        self.c1.append(struct.unpack("H",pmp.read(2))[0])
        self.c2.append(struct.unpack("I",pmp.read(4))[0])
        self.type2.append(struct.unpack("H",pmp.read(2))[0])
        self.c4.append(struct.unpack("H",pmp.read(2))[0])
        self.size.append(struct.unpack("I",pmp.read(4))[0])
    
        if self.magic[i] != 0x3fcccccd:
            raise PmpMagicError(
                "failed magic: (0x3fcccccd) %#x"%self.magic[i])
    
        if self.c1[i] != 0x1332:
            raise PmpMagicError("failed c1: (0x1332) %#x"%self.c1[i])
    
        if self.c2[i] != 0x00000002:
            raise PmpMagicError("failed c1: (0x00000002) %#x"%self.c2[i])
    
        if self.c4[i] != 0x1332:
            raise PmpMagicError("failed c4: (0x1332) %#x"%self.c4[i])
    
        if self.type1[i] != self.type2[i]:
            raise PmpTypeError(
                "type1 (%#x) not equal to type2 (%#x)"%
                (self.type1[i],self.type2[i]))
    
    
    def doStrings(self,pmp,columnName):
        '''
        Read null terminated strings into dictionary data[columnName][x]
        
        '''
        
        self.data[columnName] = []
        self.sValue = ""
        while True:
            b = pmp.read(1)
            if len(b) == 0: # EOF
                return len(self.data[columnName])
            elif b == chr(0):   # EOS
                self.data[columnName].append(self.sValue)
                self.sValue = ""
            else:
                self.sValue += b

    
    def doUint(self,pmp,columnName,size):
        '''
        Read unsigned ints into dictionary data[columnName][x]
        
        '''
        
        self.data[columnName] = array.array('I')
        try:
            # request 2x what I expect to force an error if the file is short
            self.data[columnName].fromfile(pmp,size*2)
        except EOFError:
            return len(self.data[columnName])
            
    
    def doUshort(self,pmp,columnName,size):
        '''
        Read unsigned short's into dictionary data[columnName][x]
        
        '''

        self.data[columnName] = array.array('H')
        try:
            # request 2x what I expect to force an error if the file is short
            self.data[columnName].fromfile(pmp,size*2)
        except EOFError:
            return len(self.data[columnName])
            
    
    def doByte(self,pmp,columnName,size):
        '''
        Read bytes into dictionary data[columnName][x]
        
        '''
        
        self.data[columnName] = array.array('B')
        try:
            # request 2x what I expect to force an error if the file is short
            self.data[columnName].fromfile(pmp,size*2)
        except EOFError:
            return len(self.data[columnName])
            
    
    def doUlong(self,pmp,columnName,size):
        '''
        Read unsigned long's into dictionary data[columnName][x]
        
        '''
        
        self.data[columnName] = array.array('L')
        try:
            # request 2x what I expect to force an error if the file is short
            self.data[columnName].fromfile(pmp,size*2)
        except EOFError:
            return len(self.data[columnName])
            
    
    
    def doFloat(self,pmp,columnName,size):
        '''
        Read float values into dictionary data[columnName][x]
        
        '''        
    
        self.data[columnName] = array.array('d')
        try:
            # request 2x what I expect to force an error if the file is short
            self.data[columnName].fromfile(pmp,size*2)          
        except EOFError:
            return len(self.data[columnName])
    
    

    def variantTime(self,varT):
        '''
        Return a floating point number as variant time (offset from 
        1899:12:30 24:00)
        
        '''
        
        day0 = 693594    # 1899 Dec 30
        
        # time zero is 1899 Dec 30 24:00.  So a time of -0.5 would be noon on 
        # Dec 30 and a time of 0.5 would be noon on Dec 31.
        
        # day: just +/- the integer offset
        newDay = day0 + int(varT)
        
        # time:  
        #    if -0.25, .75 of current day
        #    if +0.25, .25 of next day
        # but we have already masked off the day, so it is just the fractional
        # part, if pos, offset from time 0:00 and if neg offset from time 
        # 24:00
        newTime = math.modf(varT)[0]
        if newTime < 0:
            newTime = 1.0 + newTime
        
        
        t,hours= math.modf(24.0*newTime)    # fractional hours, hours
        t,minutes= math.modf(60.0*t)        # fractional minutes, minutes
        seconds = int(60.0*t)               # seconds, discarding fractional

        d = datetime.date.fromordinal(int(newDay))
        t = datetime.time(int(hours), int(minutes), seconds)
        dt = datetime.datetime.combine(d, t)
        
        return dt.isoformat()
 
 
    def colSizes(self):
        '''
        Return a list of tuples [ (columname, size), (...), ... ]
        
        '''
        
        return zip(self.columns,self.size)
       
 
    def getEntry(self,index):
        '''
        Return the entry in the form:
        [ col1name=val1, col2name=val2, ... ]
        .
        .
        .
        
        '''
        ret = []
        if index >= 0:
            for i in range(len(self.columns)):
                if index < self.size[i]:
                    ret.append(self.data[self.columns[i]][index])
                else:
                    ret.append("")
        
        return zip(self.columns,ret)
                 
 
 
        