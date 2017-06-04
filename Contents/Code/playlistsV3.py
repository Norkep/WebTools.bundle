######################################################################################################################
#	Playlist module unit					
#
#	Author: dane22, a Plex Community member
#
# A WebTools module for handling playlists
#
######################################################################################################################
import time
import json
from misc import misc
import datetime
from plextvhelper import plexTV
import re
#TODO: Remove when Plex framework allows token in the header. Also look at delete and list method
import urllib2
from xml.etree import ElementTree
#import requests
#TODO End


GET = ['LIST', 'DOWNLOAD']
PUT = []
POST = ['COPY', 'IMPORT']
DELETE = ['DELETE']

class playlistsV3(object):
	# Defaults used by the rest of the class
	@classmethod
	def init(self):
		self.getListsURL = misc.GetLoopBack() + '/playlists/all'

	'''
	This metode will import a playlist 
	Takes a file that it uploads, as well as a userid as the target user		
	'''
	@classmethod
	def IMPORT(self, req, *args):
		print 'Ged Import'
		try:
			if 'file' not in req.request.files:
				Log.Critical('Missing file to upload')
				req.clear()
				req.set_status(412)			
				req.finish('Missing file to upload')
			# Get the playlist as an array of lines
			m3u8File = req.request.files['file'][0]['body'].split('\n')

			print 'Ged 1', m3u8File
			bOurList = False
			if '#Server Id' in m3u8File[4]:
				# Seems like the playlist was created by us, so we are happy, and maybe saves time here
				bOurList = True
				# Get the Id
				ServerId = m3u8File[4].split(':')[1].strip()
				# Get the length
				length = len(m3u8File)
				# Get the type
				playlistType = m3u8File[3].split(':')[1].strip()
				# Get the Name
				playlistTitle = m3u8File[2].split(':')[1].strip()
				# Is the server the same as the one that created the playlist?
				bSameServer = (ServerId == XML.ElementFromURL('http://127.0.0.1:32400/identity').get('machineIdentifier')) 
				
		
				print 'Ged 4 Id',  ServerId, length, playlistType, playlistTitle, bSameServer, bOurList



			# Walk the playlist, in order to generate the json we need for the import, but we have 4 seperate cases here: same server or not, and our list or not
			# It's a mess....SIGH.....I need a life besides a virtual one :(


	

			# Make url for creation of playlist
			targetFirstUrl = misc.GetLoopBack() + '/playlists?type=' + playlistType + '&title=' + String.Quote(playlistTitle) + '&smart=0&uri=library://'
			counter = 0


			print 'Ged 6', targetFirstUrl


			# Get user
			# Walk playlist, and add only valid stuff


		except Exception, e:
			Log.Exception('Unknown error in Pleaylist Import was %s' %(str(e)))




	''' This metode will copy a playlist. between users '''
	@classmethod
	def COPY(self, req, *args):
		users = None
		# Start by getting the key of the PlayList
		if args != None:
			# We got additional arguments
			if len(args) > 0:
				# Get them in lower case
				arguments = [item.lower() for item in list(args)[0]]
			else:
				Log.Critical('Missing Arguments')
				req.clear()
				req.set_status(412)			
				req.finish('Missing Arguments')
			# Get playlist Key
			if 'key' in arguments:
				# Get key of the user
				key = arguments[arguments.index('key') +1]
			else:
				Log.Error('Missing key of playlist')
				req.clear()
				req.set_status(412)			
				req.finish('Missing key of playlist')
			# Get UserFrom
			if 'userfrom' in arguments:
				# Get the userfrom
				userfrom = arguments[arguments.index('userfrom') +1]
			else:
				# Copy from the Owner
				userfrom = None
			# Get UserTo
			if 'userto' in arguments:
				# Get the userto
				userto = arguments[arguments.index('userto') +1]
			else:
				Log.Error('Missing target user of playlist')
				req.clear()
				req.set_status(412)			
				req.finish('Missing targetuser of playlist')
			# Get user list, among with access token
			users = plexTV().getUserList()
			# Get the playlist that needs to be copied
			url = misc.GetLoopBack() + '/playlists/' + key + '/items'
			if userfrom == None:
				# Get it from the owner
				playlist = XML.ElementFromURL(url)
			else:
				#We need to logon as specified user
				try:
					# Get user playlist
					#TODO Change to native framework call, when Plex allows token in header
					opener = urllib2.build_opener(urllib2.HTTPHandler)
					request = urllib2.Request(url)
					request.add_header('X-Plex-Token', users[userfrom]['accessToken'])
					response = opener.open(request).read()
					playlist = XML.ElementFromString(response)
				except Ex.HTTPError, e:
					Log.Exception('HTTP exception  when downloading a playlist for the owner was: %s' %(e))
					req.clear()
					req.set_status(e.code)			
					req.finish(str(e))
				except Exception, e:
					Log.Exception('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
					req.clear()
					req.set_status(500)			
					req.finish('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
			# Now walk the playlist, and do a lookup for the items, in order to grab the librarySectionUUID
			jsonItems = {}
			playlistType = playlist.get('playlistType')
			playlistTitle = playlist.get('title')
			playlistSmart = (playlist.get('smart') == 1)
			for item in playlist:
				itemKey = item.get('ratingKey')
				xmlUrl = misc.GetLoopBack() + '/library/metadata/' + itemKey
				UUID = XML.ElementFromURL(misc.GetLoopBack() + '/library/metadata/' + itemKey).get('librarySectionUUID')
				if UUID in jsonItems:
					jsonItems[UUID].append(itemKey)
				else:
					jsonItems[UUID] = []
					jsonItems[UUID].append(itemKey)
			# So we got all the info needed now from the source user, now time for the target user
			try:
				#TODO Change to native framework call, when Plex allows token in header
				urltoPlayLists = misc.GetLoopBack() + '/playlists'
				opener = urllib2.build_opener(urllib2.HTTPHandler)
				request = urllib2.Request(urltoPlayLists)
				request.add_header('X-Plex-Token', users[userto]['accessToken'])
				response = opener.open(request).read()
				playlistto = XML.ElementFromString(response)
			except Ex.HTTPError, e:
				Log.Exception('HTTP exception when downloading a playlist for the owner was: %s' %(e))
				req.clear()
				req.set_status(e.code)			
				req.finish(str(e))
			except Exception, e:
				Log.Exception('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
				req.clear()
				req.set_status(500)			
				req.finish('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
			# So we got the target users list of playlists, and if the one we need to copy already is there, we delete it
			for itemto in playlistto:
				if playlistTitle == itemto.get('title'):
					keyto = itemto.get('ratingKey')
					deletePlayLIstforUsr(req, keyto, users[userto]['accessToken'])
			# Make url for creation of playlist
			targetFirstUrl = misc.GetLoopBack() + '/playlists?type=' + playlistType + '&title=' + String.Quote(playlistTitle) + '&smart=0&uri=library://'
			counter = 0

			print 'Ged77'
			print jsonItems


			for lib in jsonItems:
				if counter < 1:
					targetFirstUrl += lib + '/directory//library/metadata/'
					medias = ','.join(map(str, jsonItems[lib])) 
					targetFirstUrl += String.Quote(medias)
					# First url for the post created, so send it, and grab the response
					try:
						opener = urllib2.build_opener(urllib2.HTTPHandler)
						request = urllib2.Request(targetFirstUrl)
						request.add_header('X-Plex-Token', users[userto]['accessToken'])
						request.get_method = lambda: 'POST'
						response = opener.open(request).read()
						ratingKey = XML.ElementFromString(response).xpath('Playlist/@ratingKey')[0]
					except Exception, e:
						Log.Exception('Exception creating first part of playlist was: %s' %(str(e)))
					counter += 1
				else:
					# Remaining as put
					medias = ','.join(map(str, jsonItems[lib])) 
					targetSecondUrl = misc.GetLoopBack() + '/playlists/' + ratingKey + '/items?uri=library://' + lib + '/directory//library/metadata/' + String.Quote(medias)
					opener = urllib2.build_opener(urllib2.HTTPHandler)
					request = urllib2.Request(targetSecondUrl)
					request.add_header('X-Plex-Token', users[userto]['accessToken'])
					request.get_method = lambda: 'PUT'
					opener.open(request)
		else:
			Log.Critical('Missing Arguments')
			req.clear()
			req.set_status(412)			
			req.finish('Missing Arguments')

	''' This metode will download a playlist. accepts a user parameter '''
	@classmethod
	def DOWNLOAD(self, req, *args):
		try:
			user = None
			if args != None:
				# We got additional arguments
				if len(args) > 0:
					# Get them in lower case
					arguments = [item.lower() for item in list(args)[0]]
					if 'user' in arguments:
						# Get key of the user
						user = arguments[arguments.index('user') +1]
				# So now user is either none (Owner) or a keyId of a user
				# Now lets get the key of the playlist
				if 'key' in arguments:
					# Get key of the user
					key = arguments[arguments.index('key') +1]
					url = misc.GetLoopBack() + '/playlists/' + key + '/items'
				else:
					Log.Error('Missing key of playlist')
					req.clear()
					req.set_status(412)			
					req.finish('Missing key of playlist')
				try:
					Log.Info('downloading playlist with ID: %s' %key)
					if user == None:
						# Get playlist from the owner					
						playlist = XML.ElementFromURL(url)
					else:
						# Get Auth token for user
						try:
							# Get user list, among with their access tokens
							users = plexTV().getUserList()	
							#TODO Change to native framework call, when Plex allows token in header
							opener = urllib2.build_opener(urllib2.HTTPHandler)
							request = urllib2.Request(url)
							request.add_header('X-Plex-Token', users[user]['accessToken'])
							response = opener.open(request).read()
							playlist = XML.ElementFromString(response)
						except Ex.HTTPError, e:
							Log.Exception('HTTP exception  when downloading a playlist for the owner was: %s' %(e))
							req.clear()
							req.set_status(e.code)			
							req.finish(str(e))
						except Exception, e:
							Log.Exception('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
							req.clear()
							req.set_status(500)			
							req.finish('Exception happened when downloading a playlist for the user was: %s' %(str(e)))
					# Get server ID
					id = XML.ElementFromURL('http://127.0.0.1:32400/identity').get('machineIdentifier')
					# Get title of playlist
					title = playlist.get('title')
					playListType = playlist.get('playlistType')
					# Replace invalid caracters for a filename with underscore
					fileName = re.sub('[\/[:#*?"<>|]', '_', title).strip() + '.m3u8'
					# Prep the download http headers
					req.set_header ('Content-Disposition', 'attachment; filename=' + fileName)
					req.set_header('Cache-Control', 'no-cache')
					req.set_header('Pragma', 'no-cache')
					req.set_header('Content-Type', 'application/text/plain')
					#start writing
					req.write(unicode('#EXTM3U') + '\n')
					req.write(unicode('#Written by WebTools for Plex') + '\n')
					req.write(unicode('#Playlist name: ' + title) + '\n')
					req.write(unicode('#Playlist type: ' + playListType) + '\n')
					req.write(unicode('#Server Id: ' + id) + '\n')
					# Lets grap the individual items
					for item in playlist:
						req.write(unicode('#{"Id":' + item.get('ratingKey') + ', "ListId":' + item.get('playlistItemID') + '}\n'))
						row = '#EXTINF:'
						# Get duration
						try:
							duration = int(item.get('duration'))/1000
						except:
							duration = -1
							pass
						row = row + str(duration) + ','
						# Audio List
						if playListType == 'audio':
							try:
								if item.get('originalTitle') == None:
									row = row + item.get('grandparentTitle').replace(' - ', ' ') + ' - ' + item.get('title').replace(' - ', ' ')
								else:
									row = row + item.get('originalTitle').replace(' - ', ' ') + ' - ' + item.get('title').replace(' - ', ' ')
								
							except Exception, e:
								Log.Exception('Exception digesting an audio entry was %s' %(str(e)))
								pass
						# Video
						elif playListType == 'video':
							try:
								entryType =  item.get('type')
								if entryType == 'movie':
									# Movie
									row = row + item.get('studio') + ' - ' + item.get('title')
								else:
									# Show
									row = row + item.get('grandparentTitle') + ' - ' + item.get('title')
							except Exception, e:
								Log.Exception('Exception happened when digesting the line for Playlist was %s' %(str(e)))
								pass
						# Pictures
						else:
							row = row + item.get('title').replace(' - ', ' ')
						# Add file path
						row = row + '\n' + item.xpath('Media/Part/@file')[0]
						req.write(unicode(row) + '\n')
					req.set_status(200)
					req.finish()
				except Ex.HTTPError, e:
					Log.Exception('HTTP exception  when downloading a playlist for the owner was: %s' %(e))
					req.clear()
					req.set_status(e.code)			
					req.finish(str(e))
				except Exception, e:
					Log.Exception('Exception happened when downloading a playlist for the owner was: %s' %(str(e)))
					req.clear()
					req.set_status(500)			
					req.finish('Exception happened when downloading a playlist for the owner was: %s' %(str(e)))
		except Exception, e:
			Log.Exception('Fatal error happened in playlists.download: ' + str(e))
			req.clear()
			req.set_status(500)			
			req.finish('Fatal error happened in playlists.download: %s' %(str(e)))
	

	''' This metode will delete a playlist. accepts a user parameter '''
	@classmethod
	def DELETE(self, req, *args):
		try:
			user = None
			if args != None:
				# We got additional arguments
				if len(args) > 0:
					# Get them in lower case
					arguments = [item.lower() for item in list(args)[0]]
					if 'user' in arguments:
						# Get key of the user
						user = arguments[arguments.index('user') +1]
				# So now user is either none (Owner) or a keyId of a user
				# Now lets get the key of the playlist
				if 'key' in arguments:
					# Get key of the user
					key = arguments[arguments.index('key') +1]
					url = misc.GetLoopBack() + '/playlists/' + key
				else:
					Log.Error('Missing key of playlist')
					req.clear()
					req.set_status(412)			
					req.finish('Missing key of playlist')
			if user == None:
				try:
					# Delete playlist from the owner					
					Log.Info('Deleting playlist with ID: %s' %key)		
					HTTP.Request(url, cacheTime=0, immediate=True, method="DELETE")
				except Ex.HTTPError, e:
					Log.Exception('HTTP exception  when deleting a playlist for the owner was: %s' %(e))
					req.clear()
					req.set_status(e.code)			
					req.finish(str(e))
				except Exception, e:
					Log.Exception('Exception happened when deleting a playlist for the owner was: %s' %(str(e)))
					req.clear()
					req.set_status(500)			
					req.finish('Exception happened when deleting a playlist for the owner was: %s' %(str(e)))
			else:
				# We need to logon as a user in order to nuke the playlist
				try:
					# Get user list, among with their access tokens
					users = plexTV().getUserList()
					# Detele the playlist	
					deletePlayLIstforUsr(req, key, users[user]['accessToken'])
				except Ex.HTTPError, e:
					Log.Exception('HTTP exception  when deleting a playlist for the owner was: %s' %(e))
					req.clear()
					req.set_status(e.code)			
					req.finish(str(e))
				except Exception, e:
					Log.Exception('Exception happened when deleting a playlist for the user was: %s' %(str(e)))
					req.clear()
					req.set_status(500)			
					req.finish('Exception happened when deleting a playlist for the user was: %s' %(str(e)))				
		except Exception, e:
			Log.Exception('Fatal error happened in playlists.delete: ' + str(e))
			req.clear()
			req.set_status(500)			
			req.finish('Fatal error happened in playlists.delete: %s' %(str(e)))

	''' This metode will return a list of playlists. accepts a user parameter '''
	@classmethod
	def LIST(self, req, *args):
		try:
			user = None
			if args != None:
				# We got additional arguments
				if len(args) > 0:
					# Get them in lower case
					arguments = [item.lower() for item in list(args)[0]]
					if 'user' in arguments:
						# Get key of the user
						user = arguments[arguments.index('user') +1]
			# So now user is either none or a keyId
			if user == None:
				playlists = XML.ElementFromURL(self.getListsURL)
			else:
				#Darn....Hard work ahead..We have to logon as another user here :-(
				users = plexTV().getUserList()	
				myHeader = {}
				myHeader['X-Plex-Token'] = users[user]['accessToken']
				#TODO Change to native framework call, when Plex allows token in header
				request = urllib2.Request(self.getListsURL, headers=myHeader)
				playlists = XML.ElementFromString(urllib2.urlopen(request).read())
#				playlists = XML.ElementFromURL(self.getListsURL, headers=myHeader)
			result = {}
			for playlist in playlists:
				id = playlist.get('ratingKey')
				result[id] = {}
				result[id]['title'] = playlist.get('title')
				result[id]['summary'] = playlist.get('summary')
				result[id]['smart'] = playlist.get('smart')
				result[id]['playlistType'] = playlist.get('playlistType')
			req.set_status(200)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish(json.dumps(result))
		except Exception, e:
			Log.Exception('Fatal error happened in playlists.list: ' + str(e))
			req.clear()
			req.set_status(500)			
			req.finish('Fatal error happened in playlists.list: %s' %(str(e)))

	''' Get the relevant function and call it with optinal params '''
	@classmethod
	def getFunction(self, metode, req):		
		self.init()
		params = req.request.uri[8:].upper().split('/')		
		self.function = None
		if metode == 'get':
			for param in params:
				if param in GET:
					self.function = param
					break
				else:
					pass
		elif metode == 'post':
			for param in params:
				if param in POST:
					self.function = param
					break
				else:
					pass
		elif metode == 'put':
			for param in params:
				if param in PUT:
					self.function = param
					break
				else:
					pass
		elif metode == 'delete':
			for param in params:
				if param in DELETE:
					self.function = param
					break
				else:
					pass
		if self.function == None:
			Log.Debug('Function to call is None')
			req.clear()
			req.set_status(404)
			req.finish('Unknown function call')
		else:		
			# Check for optional argument
			paramsStr = req.request.uri[req.request.uri.upper().find(self.function) + len(self.function):]			
			# remove starting and ending slash
			if paramsStr.endswith('/'):
				paramsStr = paramsStr[:-1]
			if paramsStr.startswith('/'):
				paramsStr = paramsStr[1:]
			# Turn into a list
			params = paramsStr.split('/')
			# If empty list, turn into None
			if params[0] == '':
				params = None
			try:
				Log.Debug('Function to call is: ' + self.function + ' with params: ' + str(params))
				if params == None:
					getattr(self, self.function)(req)
				else:
					getattr(self, self.function)(req, params)
			except Exception, e:
				Log.Exception('Exception in process of: ' + str(e))


#************************ Internal functions ************************
def deletePlayLIstforUsr(req, key, token):
	url = misc.GetLoopBack() + '/playlists/' + key
	try:
		#TODO Change to native framework call, when Plex allows token in header
		opener = urllib2.build_opener(urllib2.HTTPHandler)
		request = urllib2.Request(url)
		request.add_header('X-Plex-Token', token)
		request.get_method = lambda: 'DELETE'
		url = opener.open(request)
	except Ex.HTTPError, e:
		Log.Exception('HTTP exception  when deleting a playlist for the owner was: %s' %(e))
		req.clear()
		req.set_status(e.code)			
		req.finish(str(e))
	except Exception, e:
		Log.Exception('Exception happened when deleting a playlist for the user was: %s' %(str(e)))
		req.clear()
		req.set_status(500)			
		req.finish('Exception happened when deleting a playlist for the user was: %s' %(str(e)))
	return req

