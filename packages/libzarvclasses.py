from numpy import float128
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
    self.name=str(n)
    self.filename=str(f)
    self.length=int(l)
    self.explicit=bool(e)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)

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
  downloadability=None

  def __init__(self,n,f='',g={},sp=0,ll=0,lp=0,we=0,ws=0,d=0):
    self.name=str(n)
    self.filepath=str(f)
    self.genres=dict(g)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)
    self.whatcd_seeders=int(we)
    self.whatcd_snatches=int(ws)
    self.downloadability=float128(d)
    
  def __str__(self):
    return (self.name+
      ":\n\tfilepath : "+self.filepath+
      "\n\tgenres : "+str(self.genres)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\twhatcd seeders : "+str(self.whatcd_seeders)+
      "\n\twhatcd snatches: "+str(self.whatcd_snatches)+
      "\n\tdownloadability: "+str(self.downloadability))

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
    self.name=str(n)
    self.genres=dict(g)
    self.similar_artists=dict(sa)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)
    self.whatcd_snatches=int(ws)
    self.whatcd_seeders=int(we)
    
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

