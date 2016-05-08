from numpy import float128
# All dicts are name:val
# genres would be genre_name:similarity/applicability and so forth
class Song:

  def __init__(self,n,f='',l=0,e=False,sp=0,ll=0,lp=0,kp=0,p=0,i=0):
    self.name=str(n)
    self.filename=str(f)
    self.length=int(l)
    self.explicit=bool(e)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)
    self.kups_playcount=int(kp)
    self.popularity=float128(p)
    self.song_id = i

  def __str__(self):
    return (self.name+
      ":\n\tfilename : "+self.filename+
      "\n\tlength : "+str(self.length)+
      "\n\texplicit : "+str(self.explicit)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\tkups playcount: "+str(self.kups_playcount)+
      "\n\tpopularity : "+str(self.popularity))

class Album:

  def __init__(self,n,f='',g={},sp=0,ll=0,lp=0,we=0,ws=0,pr=0,kp=0,d=0):
    self.name=str(n)
    self.filepath=str(f)
    self.genres=dict(g)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)
    self.whatcd_seeders=int(we)
    self.whatcd_snatches=int(ws)
    self.pitchfork_rating=int(pr)
    self.kups_playcount=int(kp)
    self.popularity=float128(d)
    
  def __str__(self):
    return (self.name+
      ":\n\tfilepath : "+self.filepath+
      "\n\tgenres : "+str(self.genres)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\twhatcd seeders : "+str(self.whatcd_seeders)+
      "\n\twhatcd snatches: "+str(self.whatcd_snatches)+
      "\n\tpitchfork rating: "+str(self.pitchfork_rating)+
      "\n\tkups playcount: "+str(self.kups_playcount)+
      "\n\tpopularity: "+str(self.popularity))

class Artist:

  def __init__(self,n,g={},sa={},sp=0,ll=0,lp=0,we=0,ws=0,pr=0,kp=0,d=0):
    self.name=str(n)
    self.genres=dict(g)
    self.similar_artists=dict(sa)
    self.spotify_popularity=int(sp)
    self.lastfm_listeners=int(ll)
    self.lastfm_playcount=int(lp)
    self.whatcd_snatches=int(ws)
    self.whatcd_seeders=int(we)
    self.pitchfork_rating=int(pr)
    self.kups_playcount=int(kp)
    self.popularity=float128(d)
    
  def __str__(self):
    return (self.name+
      "\n\tgenres : "+str(self.genres)+
      "\n\tsimilar artists : "+str(self.similar_artists)+
      "\n\tspotify popularity : "+str(self.spotify_popularity)+
      "\n\tlastfm listeners : "+str(self.lastfm_listeners)+
      "\n\tlastfm playcount : "+str(self.lastfm_playcount)+
      "\n\twhatcd seeders : "+str(self.whatcd_seeders)+
      "\n\twhatcd snatches: "+str(self.whatcd_snatches)+
      "\n\tpitchfork rating: "+str(self.pitchfork_rating)+
      "\n\tkups playcount: "+str(self.kups_playcount)+
      "\n\tpopularity: "+str(self.popularity))

