#!/usr/bin/python

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

import    argparse
import    os
import    re
import    sys
import    fnmatch
from picasa3meta import thumbindex, pmpinfo, iniinfo, exiv2meta, contacts



#import pdb; pdb.set_trace()

def locatedir(pattern,start):
    '''Search for a directory'''
    for path, dirs, files in os.walk(os.path.abspath(start)):
        for d in fnmatch.filter(dirs, pattern):
            yield os.path.join(path, d)

def locate(pattern,start):
    '''Search for a file'''
    for path, dirs, files in os.walk(os.path.abspath(start)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)





def main():
    '''metaSave gives an example of using the picasa3meta modules.  It will walk an image
    directory tree and create a duplicate tree (with .meta suffix) of files containing just
    the metadata related to each image.  This was basically just an exercise in discovering
    where and how Picasa stores all it's image information but hopefully someone may find it
    useful.
     
    If the input is:
    
    ~/Pictures/
        Album1/
            image001.jpg
            image002.jpg
            
    The output would be:
    
    `pwd`/Pictures.meta/
        Album1/
            image001.jpg.meta
            image002.jpg.meta
            
    Each image.meta file will contain something along these lines:
    
        pmp.index:21431
        pmp.caption:Christmas 1978
        ...
        pmp.filters:autolight=1;autocolor=1;crop64=1,8c20842f6d7fed1;enhance=1;fill=1,0.289720;
        pmp.filters.autolight:1
        pmp.filters.autocolor:1
        pmp.filters.crop64:1,8c20842f6d7fed1
        pmp.filters.enhance:1
        pmp.filters.fill:1,0.289720
        ...
        ini.crop=rect64(8c20842f6d7fed1)
        ini.cropxy=0.034211,0.032258,0.964233,0.995392
        ...
        ini.faces=rect64(7b36048cad223d28),7a162eb10f6470eb;rect64(502f02655e191250),ffffffffffffffff;rect64(c0491903e3033e98),3f1c39c6f473ee87
        ini.sfaces="First Contact1","unknown","First Contact2"
        ini.backuphash=5473
        ini.filters=redeye=1;
        Exif.Image.Software:Picasa
        Exif.Image.ExifTag:46
        Exif.Photo.ExifVersion:2.20
        Exif.Photo.DateTimeOriginal:1978:12:25 07:58:04
        Iptc.Envelope.ModelVersion:4
        Iptc.Envelope.CharacterSet:
        Iptc.Application2.RecordVersion:4
        Iptc.Application2.DateCreated:1978-12-25
        Iptc.Application2.TimeCreated:07:58:04+00:00
        Iptc.Application2.Caption:Christmas 1978
        Xmp.exif.DateTimeOriginal:1978-12-25T07:58:04+00:00
        Xmp.dc.description:Christmas 1978

    '''
    parser = argparse.ArgumentParser(
        description="Collect all the image metadata I can find into one place.")
    parser.add_argument(
        '--path', action="store", dest='path', type=str, default="",
        help="Path to the Picasa database files. " \
        "If left off, search $HOME for directory Picasa3 containing " \
        "directories db3 and contacts")
    parser.add_argument(
        '--photos', action="store", dest="source", type=str, required=True,
        help="Path to the photo tree.  This directory tree will be "\
        "duplicated at <dest>/<basename of tree>.meta and all meta data "\
        "from the pmp databases, .picasa.ini files and exif info will be "\
        "placed there.\n**NOTHING UNDER THIS DIRECTORY WILL BE MODIFIED**")
    parser.add_argument(
        '--dest', action="store", dest="dest", type=str, default=os.getcwd(),
        help="Where to create the metadata tree.  Defaults to $CWD" )
    parser.add_argument(
        '--tweak', action="store", dest="tweak", type=str, default="",
        help="Adjust the path names used when searching the thumbindex.db "\
        " file.  What is stored in the thumbindex.db file is the full path "\
        "relative to the system it was created on.  If you have copied the "\
        "photo tree and Picasa3 files to another system or have them "\
        "remotely mounted with a different path you can use --tweak to "\
        "adjust the path. \nexample:\n\t"\
        "--tweak '/my/path/Pictures':'/thumbindex/path/Pictures'" )
    args = parser.parse_args()

    
    # in any dir = Picasa3, look for a db3 dir

    if args.path == "":
        for path in locatedir("Picasa3",os.environ['HOME']):
            if os.path.exists(os.path.join(path,"db3")) and \
                os.path.exists(os.path.join(path,"contacts")):
                args.path=path
                break

    try:
        contactFile = locate("contacts.xml",args.path).next()
        thumbfile = locate("thumbindex.db",args.path).next()
    except:
        print "error: contacts.xml and/or thumbindex.db were " \
                    "not found in any subdirectory under %s"%args.path
        return 2

    if args.path == "":
        print "no Picasa3 directory found in %s"%os.environ['HOME']
        print "please specify using --path"
    else:
        source = os.path.abspath(args.source)
        dest = os.path.abspath(
            os.path.join(args.dest,os.path.basename(source)+".meta"))
        
        if args.tweak != "":
            myPath, thumbPath = args.tweak.split(':')
        else:
            myPath = ""
            thumbPath = ""
            
        print "Picasa3 path: %s"%args.path
        print "      thumbs: %s"%thumbfile
        print "    contacts: %s"%contactFile
        print "      source: %s"%source
        print "        dest: %s"%dest
        if myPath != "":
            print "      myPath: %s"%myPath
            print "   thumbPath: %s"%thumbPath
        #print "       index: %s"%index
        
        if re.match(source,args.dest):
            print "Destination (%s) is a subdirectory of source (%s)." \
                "  To avoid recursion I require these to be different." \
                "  Please change your working directory or specify a " \
                "destination with --dest"%(args.dest,source)
            return 2

        if os.path.exists(dest):
            print "Destination (%s) already exists. "\
                "In order to be absolutely sure I do not overwrite " \
                "anything I require that the destination directory does not " \
                "previously exist. Please delete it or specify a different " \
                "destination with --dest"%dest
            return 2
       
        try:            
            print "reading imagedata pmp files ...",
            pmpDB = pmpinfo.PmpInfo(os.path.join(args.path,'db3'),'imagedata')
            print "done"
            #for K,V in pmpDB.colSizes():
            #    print "%s:%d"%(K,V)
            #for K,V in pmpDB.getEntry(20102):
            #    print "%s : %s"%(K,V)
            
            print "reading pmp index file .... ",
            picasaDb = thumbindex.ThumbIndex(thumbfile)          
            print "%d records"%picasaDb.entries           
            #for i in range(picasaDb.entries):
            #    print "%d:%s"%(i,picasaDb.imageFullName(i))
            
            print "reading contacts file ...",
            con = contacts.Contacts(contactFile)
            print "%d read"%len(con.handler.mapping)
            
            #for K in con.handler.mapping:
            #    print "contact[%s]=%s"%(K,con.getContact(K))
                
            print "reading .picasa.ini files ...",
            iniO = []
            for ini in locate(".picasa.ini", source):               
                iniO.append(iniinfo.IniInfo(ini,con))             
            print "[%d] processed"%len(iniO)
                
            print "now walking image library at %s"%source,
            print " and writing all metadata to a duplicate tree at %s ..."%dest,
            
            count = 0
            for img in locate("*",source):
                if os.path.isfile(img):
                    count += 1                  
                    iniDir = os.path.dirname(img)
                    if myPath != "":
                        pmpDir = iniDir.replace(myPath,thumbPath)
                    outDir = iniDir.replace(source,dest)
                    outBase = os.path.basename(img)                
                    outFile = os.path.join(outDir,outBase+".meta")

                    try:
                        os.makedirs(outDir,0750)
                    except:
                        pass
                    
                    oF = open(outFile,"w")
                    # pmp index
                    index = picasaDb.indexOfFile(os.path.join(pmpDir,outBase))
                    oF.write("pmp.index:%d\n"%index)  
                    # pmp info
                    for K,V in pmpDB.getEntry(index):
                        oF.write("pmp.%s:%s\n"%(K,V))
                        # for pmp column crop64, add another entry crop64.xy
                        # with the 16 digit hex converted to x1, y1, x2, y2
                        if K == "crop64":
                            mx = float(int(0xffff))
                            x1 = float((int(V)&0xffff000000000000)>>48)/mx
                            y1 = float((int(V)&0x0000ffff00000000)>>32)/mx
                            x2 = float((int(V)&0x00000000ffff0000)>>16)/mx
                            y2 = float( int(V)&0x000000000000ffff)/mx
                            oF.write("pmp.%s.xy:%f,%f,%f,%f\n"%(K,x1,y1,x2,y2))
                        # if the pmp column is filters, break the filter string
                        # out into it's elements as well
                        elif K == "filters":
                            for F in V.split(';'):
                                try:
                                    f,v = F.split('=')
                                    # for the tilt filter, convert to degrees.
                                    # I believe the tilt is +/- 10 degrees max
                                    # but this is just from trial and error
                                    if f == "tilt":
                                        q,a,r = v.split(',')
                                        if q != "1" or r != "0.000000":
                                            raise "error: unknown tilt %s"%v
                                        else:
                                            ang = -10.0*float(a)
                                            oF.write("pmp.%s.%s:%f\n"%(K,f,ang))
                                    elif f == "fill":
                                        q,r = v.split(',')
                                        if q != "1":
                                            raise "error: unknown fill %s"%v
                                        else:
                                            oF.write("pmp.%s.%s:%s\n"%(K,f,r))
                                    elif f == "crop64":
                                        q,r = v.split(',')
                                        if q != "1":
                                            raise "error: unknown crop %s"%v
                                        else:
                                            mx = float(int(0xffff))
                                            x1 = float((int(r,16)&0xffff000000000000)>>48)/mx
                                            y1 = float((int(r,16)&0x0000ffff00000000)>>32)/mx
                                            x2 = float((int(r,16)&0x00000000ffff0000)>>16)/mx
                                            y2 = float( int(r,16)&0x000000000000ffff)/mx
                                            oF.write("pmp.%s.%sxy:%f,%f,%f,%f\n"%(K,f,x1,y1,x2,y2))                             
                                    else:
                                        oF.write("pmp.%s.%s:%s\n"%(K,f,v))
                                except:
                                    #print "filter error: %s (%s)(%s)"%(F,sys.exc_info()[0],sys.exc_info()[1])
                                    pass                        
                    # ini info
                    for ini in iniO:
                        if ini.filePath == iniDir:
                            for L in ini.getFileEntry(outBase):
                                oF.write("ini.%s\n"%L)
                            break
                            
                    # and finally, exiv2 data
                    for K,V in exiv2meta.EXIV2Meta(img):
                        oF.write("%s:%s\n"%(K,V))
                    oF.close()
                    
            print "[%d] files"%count
        except:
            print "error: ",sys.exc_info()[0],":",sys.exc_info()[1]
            return 3

if __name__ == "__main__":
    sys.exit(main())
