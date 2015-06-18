import sys,os,re,datetime


cocksucker = re.compile('cock.{,12}suck')
def is_safe_harbor() :
	return (datetime.datetime.now().time() < time(6) or datetime.datetime.now().time() > time(22))

def is_explicit(text) :
	if 'fuck' in text or 'cunt' in text or cocksucker.match(text):
		return True
	return False

#def genre() :
#	now = datetime.datetime.now().time()
	## etc..
