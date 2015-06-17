
def safe_harbor :
	return (datetime.datetime.now().time() < time(6) || datetime.datetime.now().time() > time(22))

def genre :
	now = datetime.datetime.now().time()
	## etc..