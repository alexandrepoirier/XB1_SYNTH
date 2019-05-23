import wx
import socket


class DisplayInfo(wx.Frame):
    def __init__(self):
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, None, -1, "Machine Info", size=(100,100), style=style)
        self._panel = wx.Panel(self, -1)
        self._panel.SetBackgroundColour(wx.Colour(10,10,10))

        ip = socket.gethostbyname(socket.gethostname())
        name = socket.getfqdn()

        gbs = wx.GridBagSizer(vgap=5, hgap=5)

        font = wx.Font(13, family=wx.FONTFAMILY_MODERN, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD)

        title = wx.StaticText(self._panel, -1, "// MACHINE INFO //")
        title.SetFont(font)
        title.SetForegroundColour(wx.Colour(200,200,200))
        gbs.Add(title, (0,0))

        ip_text = wx.StaticText(self._panel, -1, ip)
        ip_text.SetFont(font)
        ip_text.SetForegroundColour(wx.Colour(200,200,200))
        gbs.Add(ip_text, (1,0))

        name_text = wx.StaticText(self._panel, -1, name)
        name_text.SetFont(font)
        name_text.SetForegroundColour(wx.Colour(200,200,200))
        gbs.Add(name_text, (2,0))

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.EXPAND | wx.ALL, 10)
        self._panel.SetSizerAndFit(box)
        self.SetSize(self._panel.GetSize()+(25, 35))


app = wx.App()
window = DisplayInfo()
window.Show()
app.MainLoop()
