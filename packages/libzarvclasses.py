# All dicts are name:val
# genres would be genre_name:similarity/applicability and so forth
class Song:
  name=None
  filename=None
  length=None
  explicit=None
  spotify_popularity=None
  lastfm_listeners=None
  lastfm_playcount=None

  def __init__(self,n,f='',l=0,e=False,sp=0,ll=0,lp=0):
    self.name=n
    self.filename=f
    self.length=l
    self.explicit=e
    self.spotify_popularity=sp
    self.lastfm_listeners=ll
    self.lastfm_playcount=lp

  def __str__(self):
    return (self.name+
      ":\n\tfilename : "+self.filename+
      "\n\tlength : "+str(self.length)+
      "\n\texplicit : "+str(self.explicit)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount))

class Album:
  name=None
  filepath=None
  genres=None
  spotify_popularity=None
  lastfm_listeners=None
  lastfm_playcount=None
  whatcd_seeders=None
  whatcd_snatches=None

  def __init__(self,n,f='',g={},sp=0,ll=0,lp=0,we=0,ws=0):
    self.name=n
    self.filepath=f
    self.genres=g
    self.spotify_popularity=sp
    self.lastfm_listeners=ll
    self.lastfm_playcount=lp
    self.whatcd_seeders=we
    self.whatcd_snatches=ws
    
  def __str__(self):
    return (self.name+
      ":\n\tfilepath : "+self.filepath+
      "\n\tgenres : "+str(self.genres)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\twhatcd seeders : "+str(self.whatcd_seeders)+
      "\n\twhatcd snatches: "+str(self.whatcd_snatches))

class Artist:
  name=None
  genres=None
  similar_artists=None
  spotify_popularity=None
  lastfm_listeners=None
  lastfm_playcount=None
  whatcd_seeders=None
  whatcd_snatches=None

  def __init__(self,n,g={},sa={},sp=0,ll=0,lp=0,we=0,ws=0):
    self.name=n
    self.genres=g
    self.similar_artists=sa
    self.spotify_popularity=sp
    self.lastfm_listeners=ll
    self.lastfm_playcount=lp
    self.whatcd_snatches=ws
    self.whatcd_seeders=we
    
  def __str__(self):
    return (self.name+
      "\n\tgenres : "+str(self.genres)+
      "\n\tsimilar artists : "+str(self.similar_artists)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\twhatcd seeders : "+str(self.whatcd_seeders)+
      "\n\twhatcd snatches: "+str(self.whatcd_snatches))

# class Genre:
#   name=None
#   supergenre=None
#   popularity=None

#   def __init__(self,n,s='',p=0):
#     self.name=n
#     self.supergenre=s
#     self.popularity=p

#   def __str__(self):
#     return (self.name+
#       "\n\tsupergenre: "+self.supergenre
#       "\n\tpopularity: "+self.popularity)

