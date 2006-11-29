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


class ClassParserInterface:
    """ An abstract interface for class parsers.
    
    A class parser monitors gedit documents and provides a gtk.TreeModel that contains
    the browser tree. Elements in the browser tree are called 'tags'.
    
    It can control the look of the tree and set its font, colour or
    size.
     
    It can provide a custom set of actions that will be integrated in
    the context menu of the browser when the user right clicks on it.
    """

    
    def parse(self, geditdoc): 
        """ Parse a gedit.Document and return a gtk.TreeModel. 
        
        geditdoc -- a gedit.Document
        """
        pass        
        
    def get_tag_position(self, model, path):
        """ Return the position of a tag in a file.
        
        Returns a tuple with the full file uri of the source file and the line
        number of the tag or None if the tag has no correspondance in a file.
        
        model -- a gtk.TreeModel (previously provided by parse()
        path -- a tuple containing the treepath
        """
        pass
    
        
    def get_menu(self, model, path):
        """ Return a list of gtk.Menu items for the specified tag. 
        Defaults to an empty list
        
        model -- a gtk.TreeModel
        path -- a tuple containing the treepath
        """
        return []

    
    def current_line_changed(self, doc, line):
        """ Called when the cursor points to a different line in the document.
        Can be used to monitor changes in the document.
        
        doc -- a gedit document
        line -- int
        """
        pass    
  
        
    def get_tag_at_line(self, model, doc, linenumber):
        """ Return a treepath to the tag at the given line number, or None if a
        tag can't be found.
        
        model -- a gtk.TreeModel
        doc -- a gedit document
        linenumber -- int
        """
        pass
        

    def cellrenderer(self, treeviewcolumn, cellrenderertext, treemodel, it):
        """ A cell renderer callback function that controls what the text label
        in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        pass

        
    def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
        """ A cell renderer callback function that controls what the pixmap next
        to the label in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        cellrendererpixbuf.set_property("pixbuf",None)
