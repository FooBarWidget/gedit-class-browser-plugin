# Copyright (C) 2006 Frederic Back (fredericback@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, 
# Boston, MA 02111-1307, USA.

import gtk
import gobject
import gedit
import options
import imagelibrary

class ClassBrowser( gtk.VBox ):
    """ A widget that resides in gedits side panel. """

    def __init__(self, geditwindow):
        """ geditwindow -- an instance of gedit.Window """
        
        imagelibrary.initialise()

        gtk.VBox.__init__(self)
        self.geditwindow = geditwindow

        try: self.encoding = gedit.encoding_get_current()
        except: self.encoding = gedit.gedit_encoding_get_current()

        self.active_timeout = False

        self.parser = None
        self.document_history = [] # contains tuple (doc,line,col)
        self.history_pos = 0
        self.previousline = 0

        self.back = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.back.connect("clicked",self.history_back)
        self.back.set_sensitive(False)
        self.forward = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.forward.connect("clicked",self.history_forward)
        self.forward.set_sensitive(False)

        tb = gtk.Toolbar()
        tb.add(self.back)
        tb.add(self.forward)
        #self.pack_start(tb,False,False)

        # add a treeview
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        self.browser = gtk.TreeView()
        self.browser.set_headers_visible(False)
        sw.add(self.browser)
        self.browser.connect("button_press_event",self.__onClick)
        self.pack_start(sw)

        # add a text column to the treeview
        self.column = gtk.TreeViewColumn()
        self.browser.append_column(self.column)

        self.cellrendererpixbuf = gtk.CellRendererPixbuf()
        self.column.pack_start(self.cellrendererpixbuf,False)

        self.crt = gtk.CellRendererText()
        self.column.pack_start(self.crt,False)

        # connect stuff
        self.browser.connect("row-activated",self.on_row_activated)
        self.show_all()

    def history_back(self, widget):
        if self.history_pos == 0: return
        self.history_pos -= 1
        entry = self.document_history[self.history_pos]
        self.__openDocumentAtLine( entry[0],entry[1],entry[2],False )
        if len(self.document_history) > 1: self.forward.set_sensitive(True)
        if self.history_pos <= 0: self.back.set_sensitive(False)
            
    def history_forward(self, widget):
        if self.history_pos+1 > len(self.document_history): return
        self.history_pos += 1
        entry = self.document_history[self.history_pos]
        self.__openDocumentAtLine( entry[0],entry[1],entry[2],False )
        self.back.set_sensitive(True)
        if self.history_pos+1 >= len(self.document_history):
            self.forward.set_sensitive(False)

    def set_model(self, treemodel, parser=None):
        """ set the gtk.TreeModel that contains the current class tree.
        parser must be an instance of a subclass of ClassParserInterface. """
        self.browser.set_model(treemodel)
        if parser:
            self.column.set_cell_data_func(self.crt, parser.cellrenderer)
            self.column.set_cell_data_func(self.cellrendererpixbuf, parser.pixbufrenderer)
        self.parser = parser
        self.browser.queue_draw()
                
    def on_row_activated(self, treeview, path, view_column):
        if self.parser is None: return
        try:
            path, line = self.parser.get_tag_position(self.browser.get_model(),path)
            self.__openDocumentAtLine(path, line)
        except:
            pass
        

    def __onClick(self, treeview, event):

        if event.button == 3:
            x, y = int(event.x), int(event.y)
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is None: return
            path, col, cellx, celly = pthinfo
            #treeview.grab_focus()
            #treeview.set_cursor(path)

            menu = gtk.Menu()

            tagpos = self.parser.get_tag_position(self.browser.get_model(),path)
            if tagpos is not None:
                filename, line = tagpos
                m = gtk.ImageMenuItem(gtk.STOCK_JUMP_TO)
                menu.append(m)
                m.show()
                m.connect("activate", lambda w,p,l: self.__openDocumentAtLine(p,l), filename, line )

            # add the menu items from the parser
            menuitems = self.parser.get_menu(self.browser.get_model(),path)
            for item in menuitems:
                menu.append(item)
                item.show()
                
            m = gtk.SeparatorMenuItem()
            m.show()
            menu.append( m )
            
            
            m = gtk.CheckMenuItem("autocollapse")
            menu.append(m)
            m.show()
            m.set_active( options.singleton().autocollapse )
            def setcollapse(w):
                options.singleton().autocollapse = w.get_active()
            m.connect("toggled", setcollapse )
            

            menu.popup( None, None, None, event.button, event.time)


    def __openDocumentAtLine(self, filename, line, column=1, register_history=True):
        """ open a the file specified by filename at the given line and column
        number. Line and column numbering starts at 1. """
        
        if line == 0 or column == 0:
            raise ValueError, "line and column numbers start at 1"
        
        documents = self.geditwindow.get_documents()
        found = None
        for d in documents:
            if d.get_uri() == filename:
                found = d
                break

        # open an existing tab or create a new one
        if found is not None:
            tab = gedit.tab_get_from_document(found)
            self.geditwindow.set_active_tab(tab)
            doc = tab.get_document()
            doc.begin_user_action()
            it = doc.get_iter_at_line_offset(line-1,column-1)
            doc.place_cursor(it)
            (start, end) = doc.get_bounds()
            self.geditwindow.get_active_view().scroll_to_iter(end,0.0)
            self.geditwindow.get_active_view().scroll_to_iter(it,0.0)
            self.geditwindow.get_active_view().grab_focus()
            doc.end_user_action()
        else:
            tab = self.geditwindow.create_tab_from_uri(filename,self.encoding,line,False,False)
            self.geditwindow.set_active_tab(tab)
            found = self.geditwindow.get_active_document()

        # place mark
        #it = found.get_iter_at_line(line-1)
        #mark = found.create_marker(None,"jumped_to",it)

        if register_history:
            self.document_history.append( (filename,line,column) )
            self.back.set_sensitive(True)
            self.forward.set_sensitive(False)
            self.history_pos += 1

    def on_cursor_changed(self, *args):
        """
        I need to catch changes in the cursor position to highlight the current tag
        in the class browser. Unfortunately, there is no signal that gets emitted
        *after* the cursor has been changed, so I have to use a timeout.
        """
        if not self.active_timeout:
            gobject.timeout_add(100,self.update_cursor)
            self.active_timeout = True

    def update_cursor(self, *args):
        doc = self.geditwindow.get_active_document()
        if doc and self.parser:
            it = doc.get_iter_at_mark(doc.get_insert())
            line = it.get_line()
            if line != self.previousline:
                self.previousline = line
                if options.singleton().verbose: print "current line:",line

                # pipe the current line to the parser
                self.parser.current_line_changed(self.browser.get_model(), doc, line)

                # set cursor on the tag the cursor is pointing to
                try:
                    path = self.parser.get_tag_at_line(self.browser.get_model(),doc,line)
                    if path:
                        self.browser.realize()
                        if options.singleton().autocollapse: self.browser.collapse_all()
                        self.browser.expand_to_path(path)
                        self.browser.set_cursor(path)
                        if options.singleton().verbose: print "jump to", path

                except Exception, e:
                    if options.singleton().verbose: print "no tag at line",line

        self.active_timeout = False
        return False
