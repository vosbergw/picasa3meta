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

import xml.sax


class Contacts(object):
	'''

	Read the Picasa3 contacts.xml file into a dict of the form:   

	{ id1=name1, id2=name2, ... }	

	Usage:

		from picasa3meta import contacts

		myContacts = contacts.Contacts("/path/to/Picasa3/contacts/contacts.xml")
		print "%d contacts found"%len(myContacts.handler.mapping)

		for contact_id in con.handler.mapping:
			print "id [%s] is [%s]"%(contact_id,myContacts.getContact(contact_id))

	The Picasa3 contacts.xml file has the form:   

		<contacts>
			<contact id="16hexdigits" name="First Last" display="Nickname" 
				modified_time="2011-12-12T15:09:12+01:00" local_contact="1|0">
				<subject user="" ... sync_enabled="1|0"/>
			 </contact>
			 .
			 .
			 .
		</contacts>

	'''


	def __init__(self,cFile):
		'''Initialize the contacts parser.'''
						
		self.parser = xml.sax.make_parser()
		self.handler = _ContactHandler()
		self.parser.setContentHandler(self.handler)
		self.parser.parse(cFile)
	

	def getContact(self,cid):
		'''Return the full name associated with the hex contact id'''

		if self.handler.mapping.has_key(cid):
			return self.handler.mapping[cid]
		else:
			return "unknown"



# the content handler for the contacts file

class _ContactHandler(xml.sax.handler.ContentHandler):
	'''Content handler.  Creates mappings for "id" and "name"'''

	def __init__(self):
		self.mapping = {}
 
	def startElement(self, name, attributes):
		if name == "contact":
			self.id = attributes["id"]
			self.name = attributes["name"]
 
	def endElement(self, name):
		if name == "contact":
		#	self.inTitle = 0
			self.mapping[self.id] = self.name

		
