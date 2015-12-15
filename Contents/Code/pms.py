######################################################################################################################
#	pms helper unit				
# A WebTools bundle plugin	
#
#	Author: dane22, a Plex Community member
#
#
######################################################################################################################
import shutil
import time, json

class pms(object):
	# Defaults used by the rest of the class
	def __init__(self):
		self.LOGDIR = os.path.join(Core.app_support_path, 'Logs')

	''' Grap the tornado req, and process it for a GET request'''
	def reqprocess(self, req):		
		function = req.get_argument('function', 'missing')
		if function == 'missing':
			req.clear()
			req.set_status(412)
			req.finish("<html><body>Missing function parameter</body></html>")
		elif function == 'getSectionsList':
			return self.getSectionsList(req)
		elif function == 'getSectionSize':
			return self.getSectionSize(req)
		elif function == 'getSection':
			return self.getSection(req)
		elif function == 'getSubtitles':
			return self.getSubtitles(req)
		elif function == 'showSubtitle':
			return self.showSubtitle(req)
		elif function == 'tvShow':
			return self.TVshow(req)
		else:
			req.clear()
			req.set_status(412)
			req.finish("<html><body>Unknown function call</body></html>")

	''' Grap the tornado req, and process it for a GET request'''
	def reqprocessDelete(self, req):		
		function = req.get_argument('function', 'missing')
		if function == 'missing':
			req.clear()
			req.set_status(412)
			req.finish("<html><body>Missing function parameter</body></html>")
		elif function == 'delSub':
			return self.delSub(req)
		else:
			req.clear()
			req.set_status(412)
			req.finish("<html><body>Unknown function call</body></html>")

	# Delete subtitle
	def delSub(self, req):
		print 'GED Del Sub'
		Log.Debug('Delete subtitle requested')
		try:
			# Start by checking if we got what it takes ;-)
			key = req.get_argument('key', 'missing')
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish("<html><body>Missing key to media</body></html>")
				return req
			subKey = req.get_argument('subKey', 'missing')
			if subKey == 'missing':
				req.clear()
				req.set_status(412)
				req.finish("<html><body>Missing subKey to subtitle</body></html>")
				return req
			myURL='http://127.0.0.1:32400/library/metadata/' + key + '/tree'
			# Grap the sub
			sub = XML.ElementFromURL(myURL).xpath('//MediaStream[@id=' + subKey + ']')
			if len(sub) > 0:
				# Sub did exists, but does it have an url?
				filePath = sub[0].get('url')							
				if not filePath:
					# Got an embedded sub here
					Log.Debug('Fatal error happened in delSub, subtitle not found')
					req.clear()
					req.set_status(406)
					req.set_header('Content-Type', 'application/json; charset=utf-8')
					req.finish('Hmmm....This is invalid, and most likely due to trying to delete an embedded sub :-)')
				else:
					if filePath.startswith('media://'):
						'''
	Here we look at an agent provided subtitle, so this part of the function 
	has been crippled on purpose
						'''
						filePath = filePath.replace('media:/', os.path.join(Core.app_support_path, 'Media', 'localhost'))
						# Subtitle name
						agent, sub = filePath.split('_')
						tmp, agent = agent.split('com.')
						# Agent used
						agent = 'com.' + agent				
						filePath2 = filePath.replace('Contents', 'Subtitle Contributions')
						filePath2, language = filePath2.split('Subtitles')
						language = language[1:3]	
						filePath3 = os.path.join(filePath2[:-1], agent, language, sub)

						''' This is removed from the code, due to the fact, that Plex will re-download right after the deletion

						subtitlesXMLPath, tmp = filePath.split('Contents')
						agentXMLPath = os.path.join(subtitlesXMLPath, 'Contents', 'Subtitle Contributions', agent + '.xml')							
						subtitlesXMLPath = os.path.join(subtitlesXMLPath, 'Contents', 'Subtitles.xml')
						self.DelFromXML(agentXMLPath, 'media', sub)
						self.DelFromXML(subtitlesXMLPath, 'media', sub)
						agentXML = XML.ElementFromURL('"' + agentXMLPath + '"')
						#Let's refresh the media
						url = 'http://127.0.0.1:32400/library/metadata/' + params['param2'] + '/refresh&force=1'
						refresh = HTTP.Request(url, immediate=False)

						# Nuke the actual file
						try:
							# Delete the actual file
							os.remove(filePath)
							print 'Removing: ' + filePath

							os.remove(filePath3)
							print 'Removing: ' + filePath3
							# Refresh the subtitles in Plex
							self.getSubTitles(params)
						except:
							return 500
						'''

						retValues = {}
						retValues['FilePath']=filePath3
						retValues['SymbLink']=filePath

						Log.Debug('Agent subtitle returning %s' %(retValues))
						req.clear()
						req.set_status(200)
						req.set_header('Content-Type', 'application/json; charset=utf-8')
						req.finish(json.dumps(retValues))
						return req
					elif filePath.startswith('file://'):
						# We got a sidecar here, so killing time.....YES

						filePath = filePath.replace('file://', '')
						try:
							# Delete the actual file
							os.remove(filePath)
							retVal = {}
							retVal['Deleted file'] = filePath
							Log.Debug('Deleted the sub %s' %(filePath))
							req.clear()
							req.set_status(200)
							req.set_header('Content-Type', 'application/json; charset=utf-8')
							req.finish(json.dumps(retVal))
						except:
							# Could not find req. subtitle
							Log.Debug('Fatal error happened in delSub, when deleting %s' %(filePath))
							req.clear()
							req.set_status(404)
							req.set_header('Content-Type', 'application/json; charset=utf-8')
							req.finish('Fatal error happened in delSub, when deleting %s' %(filePath))
			else:
				# Could not find req. subtitle
				Log.Debug('Fatal error happened in delSub, subtitle not found')
				req.clear()
				req.set_status(404)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Could not find req. subtitle')
		except:
			Log.Debug('Fatal error happened in delSub')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in delSub')

	''' TVShow '''
	def TVshow(self, req):
		Log.Debug('TV Show requested')

		# Get Season contents
		def getSeason(req, key):
			try:
				bGetSubs = (req.get_argument('getSubs', 'False').upper()=='TRUE')
				Log.Debug('Got a season request')
				myURL = 'http://127.0.0.1:32400/library/metadata/' + key + '/tree'
				episodes = XML.ElementFromURL(myURL).xpath('.//MetadataItem/MetadataItem')
				mySeason = []
				for episode in episodes:
					myEpisode = {}
					myEpisode['key'] = episode.get('id')					
					myEpisode['title'] = episode.get('title')					
					myEpisode['episode'] = episode.get('index')
					if bGetSubs:
						myEpisode['subtitles'] = self.getSubtitles(req, mediaKey=myEpisode['key'])
					mySeason.append(myEpisode)
				Log.Debug('returning: %s' %(mySeason))
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(json.dumps(mySeason))
			except:
				Log.Debug('Fatal error happened in TV-Show while fetching season')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in TV-Show while fetching season')


		# Get Seasons list
		def getSeasons(req, key):
			try:
				myURL = 'http://127.0.0.1:32400/library/metadata/' + key + '/children'				
				mySeasons = []
				seasons = XML.ElementFromURL(myURL).xpath('//Directory')
				for season in seasons:
					if season.get('ratingKey'):
						mySeason = {}
						mySeason['title'] = season.get('title')
						mySeason['key'] = season.get('ratingKey')					
						mySeason['season'] = season.get('index')
						mySeason['size'] = season.get('leafCount')					
						mySeasons.append(mySeason)
				Log.Debug('Returning seasons as %s' %(mySeasons))
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(str(json.dumps(mySeasons)))
			except:
				Log.Debug('Fatal error happened in TV-Show while fetching seasons')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in TV-Show while fetching seasons')


		# Get Size function
		def getSize(req, key):
			Log.Debug('Get TV-Show Size req. for %s' %(key))
			# Grap TV-Show size
			myURL = 'http://127.0.0.1:32400/library/metadata/' + key + '/allLeaves?X-Plex-Container-Start=0&X-Plex-Container-Size=0'
			try:
				size = XML.ElementFromURL(myURL).get('totalSize')		
				Log.Debug('Returning size as %s' %(size))
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(size)
			except:
				Log.Debug('Fatal error happened in TV-Show while fetching size')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in TV-Show while fetching size')

		# Get Contents
		def getContents(req, key):
			try:
				# Start of items to grap
				start = req.get_argument('start', 'missing')
				if start == 'missing':
					req.clear()
					req.set_status(412)
					req.finish('You are missing start param')
					return req
				# Amount of items to grap
				size = req.get_argument('size', 'missing')
				if size == 'missing':
					req.clear()
					req.set_status(412)
					req.finish("You are missing size param")
					return req
				# Get subs info as well ?
				bGetSubs = (req.get_argument('getSubs', 'False').upper()=='TRUE')
				myURL = 'http://127.0.0.1:32400/library/metadata/' + key + '/allLeaves?X-Plex-Container-Start=' + start + '&X-Plex-Container-Size=' + size
				shows = XML.ElementFromURL(myURL).xpath('//Video')
				episodes=[]
				for media in shows:
					episode = {}
					episode['key'] = media.get('ratingKey')
					episode['title'] = media.get('title')
					episode['season'] = media.get('parentIndex')
					episode['episode'] = media.get('index')
					if bGetSubs:
						episode['subtitles'] = self.getSubtitles(req, mediaKey=episode['key'])
					episodes.append(episode)					
				Log.Debug('Returning episodes as %s' %(episodes))
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(json.dumps(episodes))
			except:
				Log.Debug('Fatal error happened in TV-Show while fetching contents')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in TV-Show while fetching contents')

		# Main func
		try:
			Log.Debug('Start TV Show')
			key = req.get_argument('key', 'missing')
			Log.Debug('Show key is %s' %(key))
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing key of Show')
				return req
			action = req.get_argument('action', 'missing')
			Log.Debug('Show action is %s' %(action))
			if action == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing action param of Show')
				return req
			# Let's follow the action here
			if action == 'getSize':
				getSize(req, key)
			elif action == 'getContents':
				getContents(req, key)
			elif action == 'getSeasons':
				getSeasons(req, key)
			elif action == 'getSeason':
				getSeason(req, key)
			else:
				Log.Debug('Unknown action for TVshow')
				req.clear()
				req.set_status(412)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Unknown action for TVshow')		
		except:
			Log.Debug('Fatal error happened in TVshow')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in TVshow')

	''' Show Subtitle '''
	def showSubtitle(self, req):
		Log.Debug('Show Subtitle requested')
		try:
			key = req.get_argument('key', 'missing')
			Log.Debug('Subtitle key is %s' %(key))
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing key of subtitle')
				return req
			myURL='http://127.0.0.1:32400/library/streams/' + key
			try:
				response = HTML.StringFromElement(HTML.ElementFromURL(myURL))
				response = response.replace('<p>', '',1)
				response = response.replace('</p>', '',1)
				response = response.replace('&gt;', '>')
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(response)
			except:
				Log.Debug('Fatal error happened in showSubtitle')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in showSubtitle')
		except:
			Log.Debug('Fatal error happened in showSubtitle')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in showSubtitle')

	''' get Subtitles '''
	def getSubtitles(self, req, mediaKey=''):
		Log.Debug('Subtitles requested')
		try:
			if mediaKey != '':
				key = mediaKey
			else:
				key = req.get_argument('key', 'missing')
			Log.Debug('Media rating key is %s' %(key))
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing rating key of media')
				return req
			getFile = req.get_argument('getFile', 'missing')
			Log.Debug('getFile is %s' %(getFile))
			# Path to media
			myURL='http://127.0.0.1:32400/library/metadata/' + key
			mediaInfo = []
			try:
				bDoGetTree = True
				# Only grap subtitle here
				streams = XML.ElementFromURL(myURL).xpath('//Stream[@streamType="3"]')					
				for stream in streams:
					subInfo = {}
					subInfo['key'] = stream.get('id')
					subInfo['codec'] = stream.get('codec')
					subInfo['selected'] = stream.get('selected')
					subInfo['languageCode'] = stream.get('languageCode')
					if stream.get('key') == None:
						location = 'Embedded'
					elif stream.get('format') == '':
						location = 'Agent'
					else:
						location = 'Sidecar'									
					subInfo['location'] = location
					# Get tree info, if not already done so, and if it's a none embedded srt, and we asked for all
					if getFile == 'true':
						if location != None:
							if bDoGetTree:							
								MediaStreams = XML.ElementFromURL(myURL + '/tree').xpath('//MediaStream')
								bDoGetTree = False
					if getFile == 'true':
						try:								
							for mediaStream in MediaStreams:				
								if mediaStream.get('id') == subInfo['key']:									
									subInfo['url'] = mediaStream.get('url')
						except:
							Log.Debug('Fatal error happened in getSubtitles')
							req.clear()
							req.set_status(500)
							req.set_header('Content-Type', 'application/json; charset=utf-8')
							req.finish('Fatal error happened in getSubtitles')
					mediaInfo.append(subInfo)	
			except:
				Log.Debug('Fatal error happened in getSubtitles')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in getSubtitles')
			if mediaKey != '':
				return str(mediaInfo)
			else:
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(json.dumps(mediaInfo))
		except:
			Log.Debug('Fatal error happened in getSubtitles')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in getSubtitles')

	''' get section '''
	def getSection(self,req):
		Log.Debug('Section requested')
		try:
			key = req.get_argument('key', 'missing')
			Log.Debug('Section key is %s' %(key))
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing key of section')
				return req
			start = req.get_argument('start', 'missing')
			Log.Debug('Section start is %s' %(start))
			if start == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing start of section')
				return req
			size = req.get_argument('size', 'missing')
			Log.Debug('Section size is %s' %(size))
			if size == 'missing':
				req.clear()
				req.set_status(412)
				req.finish('Missing size of section')
				return req
			getSubs = req.get_argument('getSubs', 'missing')
			# Got all the needed params, so lets grap the contents
			try:
				myURL = 'http://127.0.0.1:32400/library/sections/' + key + '/all?X-Plex-Container-Start=' + start + '&X-Plex-Container-Size=' + size
				rawSection = XML.ElementFromURL(myURL)
				Section=[]
				for media in rawSection:
					if getSubs != 'true':
						media = {'key':media.get('ratingKey'), 'title':media.get('title')}
					else:
						subtitles = self.getSubtitles(req, mediaKey=media.get('ratingKey'))
						media = {'key':media.get('ratingKey'), 'title':media.get('title'), 'subtitles':subtitles}
					Section.append(media)					
				Log.Debug('Returning %s' %(Section))
				req.clear()
				req.set_status(200)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish(json.dumps(Section))
			except:
				Log.Debug('Fatal error happened in getSection')
				req.clear()
				req.set_status(500)
				req.set_header('Content-Type', 'application/json; charset=utf-8')
				req.finish('Fatal error happened in getSection')
		except:
			Log.Debug('Fatal error happened in getSection')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in getSection')

	''' get sections list '''
	def getSectionsList(self,req):
		Log.Debug('Sections requested')
		try:
			rawSections = XML.ElementFromURL('http://127.0.0.1:32400/library/sections')
			Sections=[]
			for directory in rawSections:
				Section = {'key':directory.get('key'),'title':directory.get('title'),'type':directory.get('type')}
				Sections.append(Section)
			Log.Debug('Returning Sectionlist as %s' %(Sections))
			req.clear()
			req.set_status(200)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish(json.dumps(Sections))
		except:
			Log.Debug('Fatal error happened in getSectionsList')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in getSectionsList')

	''' Get a section size '''
	def getSectionSize(self, req):
		Log.Debug('Retrieve Section size')
		try:
			key = req.get_argument('key', 'missing')
			Log.Debug('Section key is %s' %(key))
			if key == 'missing':
				req.clear()
				req.set_status(412)
				req.finish("<html><body>Missing key of section</body></html>")
				return req
			else:
				myURL = 'http://127.0.0.1:32400/library/sections/' + key + '/all?X-Plex-Container-Start=0&X-Plex-Container-Size=0'
				try:
					section = XML.ElementFromURL(myURL)
					Log.Debug('Returning size as %s' %(section.get('totalSize')))
					req.clear()
					req.set_status(200)
					req.finish(section.get('totalSize'))
				except:					
					Log.Debug('Fatal error happened in GetSectionSize')
					req.clear()
					req.set_status(500)
					req.set_header('Content-Type', 'application/json; charset=utf-8')
					req.finish('Fatal error happened in GetSectionSize')
		except:
			Log.Debug('Fatal error happened in getSectionSize')
			req.clear()
			req.set_status(500)
			req.set_header('Content-Type', 'application/json; charset=utf-8')
			req.finish('Fatal error happened in getSectionSize')


