#   geditBRM.py
#   A bicycleRepairMan implementation for gedit
#
# The code is based on the Bicycle Repair Man integration for (X)Emacs
# by Phil Dawes (2002)
#
# Copyright (C) 2005-2006 Frederic Back 
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

"""
A wrapper module around the BicycleRepairMan functions.
This is not a gedit plugin, but a module to be used by gedit plugins.

Note that the implementation might get a bit ugly sometimes, because the high
level API of BRM is pretty dirty.
"""

import sys
import os
import os.path
import gtk
import bike
import gedit

class BikeLogger:
    def __init__(self):
        pass

    def write(self, text):
        #print ">>>",text,"<<<"
        pass

#-------------------------------------------------------------------------------
class geditBRM:
    """ A BicycleRepairMan wrapper for Gedit. """

    def __init__(self, window):
        self.ctx = bike.init()

        self.tmpBufferPath = '/tmp/gedit_bicyclerepairman_buffer.py'
        self.window = window
        self.encoding = gedit.gedit_encoding_get_current()

        self.logger = BikeLogger()
        self.ctx.setProgressLogger(self.logger)
        self.ctx.setWarningLogger(self.logger)

    #---------------------------------------------------------------------------

    def findReferences(self, filename, line, column):
        references = []
        try:
            refs = self.ctx.findReferencesByCoordinates(filename,line,column)
            # pack refs into a simple list: BRM stuff is too mystical for me,
            # for example, the exception is cast *during the next operation*.
            for ref in refs:
                references.append( (ref.filename,ref.lineno,ref.confidence) )
        except bike.query.findReferences.CouldntFindDefinitionException:
            self.__errorMessage(
                "Could not search for references",
                "Please select a function or class definition")
        except bike.query.common.CouldNotLocateNodeException, e:
            self.__errorMessage(
                "Could not search for references",
                "Please select a function or class definition")
        return references


    def findReferencesDialog(self, widget, win):
        """ Find the places where a selected function is referenced. """

        # get active document
        doc = self.window.get_active_document()
        docfilename = doc.get_uri_for_display()

        # get current selection
        try: (selectionStart,selectionEnd) = doc.get_selection_bounds()
        except ValueError, e: selectionStart = selectionEnd = None
        if selectionStart == selectionEnd:
            self.__errorMessage("Could not search for references",
                "You have to select a class declaration\nor a function definition.",
                win)
        line = selectionStart.get_line() + 1
        column = selectionStart.get_line_offset() + 1

        references = self.findReferences(docfilename,line,column)

        # display a list of references in a dialog
        if len(references) == 0: return
        dialog = gtk.Dialog("References found...",None,0,())
        treeview = gtk.TreeView(gtk.ListStore(str,int,str))
        crt = gtk.CellRendererText()
        #crt.set_property("width-chars",40)
        treeview.append_column( gtk.TreeViewColumn("file", crt, text=0) )
        treeview.append_column( gtk.TreeViewColumn("line", crt, text=1) )
        treeview.append_column( gtk.TreeViewColumn("probability", crt, text=2) )
        sw = gtk.ScrolledWindow()
        sw.add(treeview)
        sw.set_shadow_type(gtk.SHADOW_IN)
        dialog.vbox.pack_start(sw)
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        #sw.set_size_request(480,-1)
        
        # add references to treeview
        for (filename, line, confidence) in references:
            f = filename
            if os.path.dirname(docfilename) == os.path.dirname(filename):
                f = os.path.basename(f)
            treeview.get_model().append( (f,line,"%i%%"%confidence) )

        dialog.set_default_size(360,240)
        dialog.add_button(gtk.STOCK_JUMP_TO,1)
        dialog.add_button(gtk.STOCK_CLOSE, 0)
        dialog.show_all()

        def jumpToReference(tv, path, view_column):
            self.__openDocumentAtLine(references[path[0]][0],references[path[0]][1],1)
            dialog.present()
        
        treeview.connect("row-activated",jumpToReference)

        while dialog.run() != 0: # loop until closed
            path, col = treeview.get_cursor()
            jumpToReference(treeview, path, col)
        dialog.destroy()

    #---------------------------------------------------------------------------
    def findDefinition(self, widget, win):
        """ tries to find the definition of a selected function or class.
            Jumps to the line of the declaration. """

        # get active document
        doc = self.window.get_active_document()

        # get current selection
        try: (selectionStart,selectionEnd) = doc.get_selection_bounds()
        except ValueError, e: selectionStart = selectionEnd = None
        if selectionStart == selectionEnd:
            self.__errorMessage("Could not search for references",
                "You have to select a class or a function call.",
                win)
        line = selectionStart.get_line() + 1
        column = selectionStart.get_line_offset() + 1
    
        # BicycleRepairMan
        try: 
            filename = self.__getDocumentFilepath(doc)
            defns = self.ctx.findDefinitionByCoordinates(filename,line,column)
        except Exception, e:
            self.__errorMessage("A BicycleRepairMan Exception occurred."%filename,e)

        try:
            a = defns.next()
            print "found in: ",a.filename,"at,",a.lineno,a.colno
            self.__openDocumentAtLine( a.filename, a.lineno, a.colno)
        except StopIteration:
            pass
        except bike.query.common.CouldNotLocateNodeException:
            self.__errorMessage(
                "Could not find the definition",
                "Please select a function or class.") 


    #---------------------------------------------------------------------------
    def renameSelection(self, widget, win):
        """ display a dialog to rename a selected class/fn/method"""

        # get data
        doc = self.window.get_active_document()
        (docStart,docEnd) = doc.get_bounds()
        (selectionStart,selectionEnd) = doc.get_selection_bounds()
        line = selectionStart.get_line() + 1
        column = selectionStart.get_line_offset() + 1
        functionName = doc.get_text(selectionStart,selectionEnd)        

        # get confirmation
        d = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL,
            "This operation will modify files directly.\nAre you sure you would like to proceed?")
        a = d.run()
        d.destroy()
        if a != gtk.RESPONSE_OK: return

        # ask for the new name
        dialog = gtk.Dialog("Enter a new name",None,0,(gtk.STOCK_OK, 1, gtk.STOCK_CANCEL, 0))
        entry = gtk.Entry()
        entry.set_text(functionName)
        dialog.vbox.pack_start(entry)
        entry.show()
        response = dialog.run()

        if response != 1: return

        #self.__saveDocumentToTempfile(doc)
        filename = doc.get_uri_for_display()

        # rename and catch exceptions
        try:
            newname = entry.get_text()
            print "Rename %s to %s"%(functionName,newname)
            print "Pos",line, column
            self.ctx.setRenameMethodPromptCallback(self.renamePrompt)
            self.ctx.renameByCoordinates(filename,line,column,newname)
        except Exception, e:
            print e

        # commit changes
        self.ctx.save()
        #self.__getChangesFromTemp(self.window,doc,line-1,column-1)
        dialog.destroy()

    def renamePrompt(self, filename, linenumber, begincolumn, endcolumn):
        print "unsure about this:"
        print filename, linenumber, begincolumn, endcolumn
        return True

    def __openDocumentAtLine(self, filename, line, column):
        documents = self.window.get_documents()
        found = None
        for d in documents:
            if d.get_uri_for_display() == filename:
                found = d
                break

        # open an existing tab or create a new one
        if found is not None:
            tab = gedit.gedit_tab_get_from_document(found)
            self.window.set_active_tab(tab)
            doc = tab.get_document()
            doc.begin_user_action()
            it = doc.get_iter_at_line_offset(line-1,column-1)
            doc.place_cursor(it)
            (start, end) = doc.get_bounds()
            self.window.get_active_view().scroll_to_iter(end,0.0)
            self.window.get_active_view().scroll_to_iter(it,0.0)
            self.window.get_active_view().grab_focus()
            doc.end_user_action()
        else:
            uri = "file://"+ filename
            tab = self.window.create_tab_from_uri(uri,self.encoding,line,False,False)
            self.window.set_active_tab(tab)


    def __saveDocumentToTempfile(self, textBuffer):
        """ copy the content of a textbuffer to a temp file """
        f = open(self.tmpBufferPath, 'w')
        buf = textBuffer.get_text(*textBuffer.get_bounds())
        f.write( buf )
        f.close()


    def __getDocumentFilepath(self, document):
        filename = document.get_uri_for_display()
        if not os.access(filename,os.R_OK):
            self.__errorMessage("BicycleRepairMan could not access %s."%filename)
        return filename


    def __errorMessage(self, title, message = None, win=None):
        d = gtk.MessageDialog(win,
            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
            str(title) )
        if message is not None: d.format_secondary_text(str(message))
        d.run()
        d.destroy()


    def __getChangesFromTemp(self,win,doc,line,column):
        # get buffer from temp file
        f = open(self.tmpBufferPath, 'r')
        buf = f.read()
        f.close()

        # replace active document by temp buffer

        # Note: When running set_text, the plugins' update_ui
        # function will be called WHILE THE DOCUMENT IS EMPTY.
        # I should report a bug.
        doc.set_text(buf)

        # go back to initial position
        try: # offset might be off in certain cases, catch!
            it = doc.get_iter_at_line_offset(line,column) 
            doc.begin_user_action()
            doc.place_cursor(it)
            self.window.get_active_view().scroll_to_iter(it,0.2)
            self.window.get_active_view().grab_focus()
            doc.end_user_action()
        except Exception, e:
            print e

        # delete temp file
        os.remove(self.tmpBufferPath)

        print "BRM done."


