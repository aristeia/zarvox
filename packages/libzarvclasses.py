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
    name=n
    filename=f
    length=l
    explicit=e
    spotify_popularity=sp
    lastfm_listeners=ll
    lastfm_playcount=lp

  def __str__(self):
    return (self.name+
      ":\n\tfilename : "+self.filename+
      "\n\tlength : "+self.length+
      "\n\texplicit : "+self.explicit+
      "\n\tspotify popularity : "+self.spotify_popularity+
      "\n\tlastfm listeners : "+self.lastfm_listeners+
      "\n\tlastfm playcount : "+self.lastfm_playcount)

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
    name=n
    filepath=f
    genres=g
    spotify_popularity=sp
    lastfm_listeners=ll
    lastfm_playcount=lp
    whatcd_seeders=we
    whatcd_snatches=ws
    
  def __str__(self):
    return (self.name+
      ":\n\tfilepath : "+self.filepath+
      "\n\tgenres : "+self.genres+
      "\n\tspotify popularity : "+self.spotify_popularity+
      "\n\tlastfm listeners : "+self.lastfm_listeners+
      "\n\tlastfm playcount : "+self.lastfm_playcount+
      "\n\twhatcd seeders : "+self.whatcd_seeders+
      "\n\twhatcd snatches: "+self.whatcd_snatches)

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
    name=n
    genres=g
    similar_artists=sa
    spotify_popularity=sp
    lastfm_listeners=ll
    lastfm_playcount=lp
    whatcd_snatches=ws
    whatcd_seeders=we
    
  def __str__(self):
    return (self.name+
      "\n\tgenres : "+self.genres+
      "\n\tsimilar artists : "+self.similar_artists+
      "\n\tspotify popularity : "+self.spotify_popularity+
      "\n\tlastfm listeners : "+self.lastfm_listeners+
      "\n\tlastfm playcount : "+self.lastfm_playcount+
      "\n\twhatcd seeders : "+self.whatcd_seeders+
      "\n\twhatcd snatches: "+self.whatcd_snatches)

# class Genre:
#   name=None
#   supergenre=None
#   popularity=None

#   def __init__(self,n,s='',p=0):
#     name=n
#     supergenre=s
#     popularity=p

#   def __str__(self):
#     return (self.name+
#       "\n\tsupergenre: "+self.supergenre
#       "\n\tpopularity: "+self.popularity)

