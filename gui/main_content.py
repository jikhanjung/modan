#import wx
import wx.html
#import os, re 
#from string import atoi
from libpy.conf import ModanConf   
#from libpy.model_mdobject import MdObject
 
LabelSize = (100,15)
 
class MdObjectContent(wx.html.HtmlWindow):
  def __init__(self, parent, id):
    window_style = wx.html.HW_SCROLLBAR_AUTO
    super(MdObjectContent, self).__init__(parent, id, 
                                              style=window_style)
    mdconf = ModanConf()
    self.conf = mdconf.item
    if 'gtk2' in wx.PlatformInfo:
      self.SetStandardFonts()

  def SetObjectContent(self, mdobject):
    self.mdobject = mdobject
    #colspan = mdobject
    lmcount = len(mdobject.landmarks)
    csize = mdobject.get_centroid_size()

    rv = "<TABLE><TR><TD BGCOLOR='blue'>"
    rv += "<FONT COLOR='white'><B>Object Name</B></FONT></TD></TR>"
    rv += "<TR><TD>"+mdobject.objname+"</TD></TR>"

    rv += "<TR><TD BGCOLOR='blue'><FONT color='white'><b>Landmarks</b></FONT>"
    rv += "</TD></TR><TR><TD BGCOLOR=#ccccff>"
    rv += "Landmark count: " + str(lmcount)
    if( csize > 0 ):
      rv += ", Centroid size: " + str( int( csize * 100 ) / 100.0 )
    rv += "</TD></TR>"
    for lm in mdobject.landmarks:
      rv+= "<TR><TH>"+str(lm.lmseq)+"</TH><TD>"+str(lm.xcoord)+"</TD><TD>"+str(lm.ycoord)+"</TD>"
      if( lm.zcoord > -99999 ):
        rv+= "<TD>" + str( lm.zcoord ) + "</TD>"
      rv+= "</TR>"
    rv+= "<tr><td colspan=4>&nbsp;</td></tr>" 
    #mdobject.bookstein_registration( 1, 2, 3 )
    #mdobject.print_landmarks("bookstein")
    #mdobject.sliding_baseline_registration( 1, 2, 3 )
    #mdobject.print_landmarks("SBR")
    #for lm in mdobject.landmarks:
    #  rv+= "<TR><TH>"+str(lm.lmseq)+"</TH><TD>"+str(lm.xcoord)+"</TD><TD>"+str(lm.ycoord)+"</TD>"
    ##  if( lm.zcoord > -99999 ):
    #    rv+= "<TD>" + str( lm.zcoord ) + "</TD>"
    #  rv+= "</TR>"
    rv += "</TABLE>"

    self.SetPage(rv)
  
  def SetBlank(self):
    self.SetPage('')
