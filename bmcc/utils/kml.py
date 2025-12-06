from lxml import etree
from lxml.builder import ElementMaker


KML_NS = "http://www.opengis.net/kml/2.2"


E = ElementMaker(namespace=KML_NS, nsmap={None: KML_NS})


class KML:
    ns = {None: "http://www.opengis.net/kml/2.2"}

    def __init__(self):
        self.root = etree.Element("kml", nsmap=self.ns)

    def document(self, parent, name):
        doc = etree.SubElement(parent, "Document", nsmap=self.ns)
        doc.text = name
        return doc

    def folder(self, parent, name):
        folder = etree.SubElement(parent, "Folder", nsmap=self.ns)
        etree.SubElement(folder, "name").text = name
        return folder

    def __str__(self):
        return etree.tostring(
            self.root,
            pretty_print=True,
            xml_declaration=True,
        ).decode("utf-8")
