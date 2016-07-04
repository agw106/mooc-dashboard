import requests,os,datetime
from bs4 import BeautifulSoup

class FLCourses:

	def __init__(self,login):
		"""Check we have Facilitator level privileges

			:param:
			    login: The BeautifulSoup Session
		"""
		self.__session  =  login
		self.__mainsite = 'https://www.futurelearn.com'
		self.__isAdmin = False
		self.__uni = ''
		admin_url = self.__mainsite + '/admin/courses'
		self.__rep = self.__session.get(admin_url, allow_redirects=True)
		
		if(self.__rep.status_code == 200):
			self.__isAdmin = True
			soup = BeautifulSoup(self.__rep.content,'html.parser')
			uni = soup.find(class_ = 'org_name')
			self.__uni = uni.text

	def getCourses(self):
		"""	Scrape the course metadata

			:return
			    courses (Dictionary) : A dictionary keyed on course name, values are themselves dictionaries of course metadata
			"""

		if(self.__isAdmin):
			webpage = self.__rep.content
			soup = BeautifulSoup(webpage,'html.parser')
			# get all courses info 
			tables = soup.findAll("table",{'class': 'table course-runs'})
			courses = {}

			for table in tables:
				for course in table.find_all('tbody'):
					course_name = course.a['title']
					print "Found course: %s ..." %course_name
					#get courses run in different time
					course_runs = course.find_all('tr')
					run_count = len(course_runs)
					print "...with %d runs" %run_count
					course_info = {}

					for course_run in course_runs:
						l = course_run.find_all('span')
						_start_date = l[0].text
						print "...start date: %s " % _start_date
						_status = l[1].text.lower()
						print "...status: %s " % _status
						_stats_path = course_run.find(title = 'View stats')['href']
						_run_details_path = course_run.find(title = 'Run details')['href']

						# Fetch data of finished courses only
						if( _status == 'finished' or _status == 'in progress' ):

							run_duration_weeks = self.getRunDuration(self.__mainsite + _run_details_path)

							# Convert to Date type and compute end date
							# Pad if needed. e.g. 9 May 2016 to 09 May 2016
							if(len(_start_date) == 10):
								_start_date = "0"+_start_date

							start_date = datetime.datetime.strptime(_start_date, "%d %b %Y")
							end_date = start_date + datetime.timedelta(weeks=int(run_duration_weeks))
							print "...end date: %s" %end_date

							run_data = {'start_date': start_date , 'end_date': end_date, 'duration_weeks' : run_duration_weeks, 'status' : _status, 'datasets' : self.getDatasets(self.__mainsite + _stats_path)}
							course_info[str(run_count)] = run_data
					
						run_count-=1

					courses[course_name] = course_info
		
			return courses
		
		else:
			return None
	

	def getDatasets(self, stats_dashboard_url):
		""" Assemble URL to datasets (CSV files)

		:param stats_dashboard_url:
		:return:
		"""

		data = {}
		
		if(self.__isAdmin):
			soup = BeautifulSoup(self.__session.get(stats_dashboard_url).content, 'html.parser')
			datasets = soup.find('ul',class_ = 'datasets')

			if(datasets):	
				links = datasets.find_all('li')

				for li in links:
					link = li.find('a')['href']
					split = str.split(str(link),'/')
					link = self.__mainsite + link
					#course_run = split[4]
					#filename = split[3]  + '_' + split[7].replace('_','-') + course_run + '.csv'
					filename = split[7].replace('_', '-')+'.csv'
					data[link] = filename
			return data



	def getRunDuration(self, _run_details_url):
		""" Find the duration of the course, in weeks

		:param _run_details_url:
		:return:
		"""
		print "Looking up duration: %s" % _run_details_url

		duration = 0
		if(self.__isAdmin):
			soup = BeautifulSoup(self.__session.get(_run_details_url).content, 'html.parser')
			run_data = soup.findAll('p',class_ = 'run-data')
			if(run_data):
				for run_datum in run_data:
					if("Duration" in run_datum.string):
						duration = run_datum.string[10:-6]
						print "Found duration: %s" % duration
		if(duration == 0):
			print("[ERROR] Unable to parse duration")
		return duration

		
	def getUniName(self):
		"""Return the institution name

		:return:
		"""
		return self.__uni