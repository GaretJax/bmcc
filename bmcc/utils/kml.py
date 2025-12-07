from lxml import etree
from lxml.builder import ElementMaker


KML_NS = "http://www.opengis.net/kml/2.2"


E = ElementMaker(namespace=KML_NS, nsmap={None: KML_NS})


class KML:
    def __init__(self):
        self.root = E.kml()

    def document(self, parent, name):
        doc = E.Document()
        doc.append(E.name(name))
        parent.append(doc)
        return doc

    def folder(self, parent, name):
        folder = E.Folder()
        folder.append(E.name(name))
        parent.append(folder)
        return folder

    def __str__(self):
        return etree.tostring(
            self.root,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        ).decode("utf-8")
