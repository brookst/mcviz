import re

from pkg_resources import resource_string, resource_exists

from .texglyph import TexGlyph


SCRIPT_TAG = re.compile('<script type="text/ecmascript" xlink:href="([^"]+)"/>')


class XMLNode(object):
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = [] if attrs is None else [attrs]
        self.children = [] if children is None else children

    def appendChild(self, child):
        self.children.append(child)

    def setAttribute(self, attr, val):
        self.attrs.append('%s="%s"' % (attr, val))

    def __str__(self):
        child_data = "".join(str(child) for child in self.children)
        open_tag = "".join(("<"," ".join([self.tag] + self.attrs),">"))
        close_tag = "".join(("</",self.tag,">"))
        return "".join((open_tag, child_data, close_tag))

class RawNode(XMLNode):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return self.data


class SVGDocument(object):
    def __init__(self, wx, wy, scale=1):

        self.scale = scale
        viewbox = "0 0 %.1f %.1f" % (wx * scale, wy * scale)
        self.svg = XMLNode("svg", 
            'version="1.1" viewBox="%s" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink"' % viewbox)
        
        # Adds a big white background rect
        self.svg.appendChild(RawNode('<rect id="background" x="0" y="0" width="%.1f" '
                                     'height="%.1f" style="fill:white;" />'
                                      % ((wx * scale), (wy * scale))))
        
        self.defs = XMLNode("defs")
        self.defined_pdgids = []
        self.svg.appendChild(self.defs)

    def add_glyph(self, pdgid, center, font_size, subscript = None):

        if not TexGlyph.exists(pdgid):
            return self.add_text_glyph(str(pdgid), center, font_size, subscript)

        x, y = center
        # Apply total scale
        font_size *= self.scale
        x *= self.scale
        y *= self.scale

        glyph = TexGlyph.from_pdgid(pdgid)
        if not pdgid in self.defined_pdgids:
            self.defs.appendChild(RawNode(glyph.xml))
            self.defined_pdgids.append(pdgid)

        if False: #options.debug_labels:
            wx, wy = glyph.dimensions
            wx *= font_size * glyph.default_scale
            wy *= font_size * glyph.default_scale

            box = XMLNode("rect")
            box.setAttribute("x", "%.3f" % (x - wx/2))
            box.setAttribute("y", "%.3f" % (y - wy/2))
            box.setAttribute("width", "%.3f" % wx)
            box.setAttribute("height", "%.3f" % wy)
            box.setAttribute("fill", "red")
            self.svg.appendChild(box)

        x -= 0.5 * (glyph.xmin + glyph.xmax) * font_size * glyph.default_scale
        y -= 0.5 * (glyph.ymin + glyph.ymax) * font_size * glyph.default_scale

        use = XMLNode("use")
        use.setAttribute("x", "%.3f" % (x/font_size))
        use.setAttribute("y", "%.3f" % (y/font_size))
        use.setAttribute("transform", "scale(%.3f)" % (font_size))
        use.setAttribute("xlink:href", "#pdg%i"%pdgid)
        self.svg.appendChild(use)

        xw = glyph.xmax * glyph.default_scale * font_size
        yw = glyph.ymax * glyph.default_scale * font_size
        self.add_subscripts(subscript, (x, y), (xw, yw), font_size)

    def add_text_glyph(self, label, center, font_size, subscript = None):

        x, y = center

        # Apply total scale
        font_size *= self.scale
        x *= self.scale
        y *= self.scale

        width_est = len(label) * font_size * 0.5 # 0.5 is a fudge factor

        if False: #options.debug_labels:
            wx, wy = width_est, font_size
            box = XMLNode("rect")
            box.setAttribute("x", "%.3f" % (x - wx/2))
            box.setAttribute("y", "%.3f" % (y - wy/2))
            box.setAttribute("width", "%.3f" % wx)
            box.setAttribute("height", "%.3f" % wy)
            box.setAttribute("fill", "red")
            self.svg.appendChild(box)
        txt = XMLNode("text")
        txt.setAttribute("x", "%.3f" % (x - width_est / 2))
        txt.setAttribute("y", "%.3f" % (y + font_size / 3)) # 3 is a fudge factor
        txt.setAttribute("font-size", "%.2f" % (font_size))
        txt.appendChild(RawNode(label))
        self.svg.appendChild(txt)

        self.add_subscripts(subscript, (x, y), (width_est/2, font_size/3), font_size)

    def add_subscripts(self, subscripts, center, dimensions, font_size):
        for subscript, pos in subscripts:
            x, y  = center
            xw, yw = dimensions
            if pos == "sub":
                x, y = x + xw, y + yw + font_size*0.1
            elif pos == "super":
                x, y = x + xw, y - font_size*0.1
            elif pos == "under":
                x, y = x - xw/2, y + yw + font_size*0.4
            elif pos == "over":
                x, y = x - xw/2, y - font_size*0.4

            txt = XMLNode("text")
            txt.setAttribute("x", "%.3f" % (x))
            txt.setAttribute("y", "%.3f" % (y))
            txt.setAttribute("font-size", "%.2f" % (font_size*0.3))
            txt.appendChild(subscript)
            self.svg.appendChild(txt)

    def add_object(self, element):
        assert not element.getAttribute("transform")
        element.setAttribute("transform", "scale(%.3f)" % (self.scale))
        self.svg.appendChild(RawNode(element.toxml()))

    def toprettyxml(self):
        return "".join(['<?xml version="1.0" encoding="ISO-8859-1"?>', str(self.svg)])


class NavigableSVGDocument(SVGDocument):
    def __init__(self, *args, **kwargs):
        super(NavigableSVGDocument, self).__init__(*args, **kwargs)
        
        # No viewbox for a NavigableSVGDocument
        self.svg.attrs = ['version="1.1" '
                          'xmlns="http://www.w3.org/2000/svg" '
                          'xmlns:xlink="http://www.w3.org/1999/xlink" '
                          'id="whole_document"']
        self.full_svg_document = self.svg
        self.svg = XMLNode("g", 'id="everything"')
        
    def toprettyxml(self):
        javascript_text = resource_string("mcviz.utils.svg.data", 
                                          "navigable_svg_fragment.xml")
                
        def match(m):
            (javascript_filename,) = m.groups()
            if not resource_exists("mcviz.utils.svg.data", javascript_filename):
                return
                
            args = "mcviz.utils.svg.data", javascript_filename
            
            # ]]> is not allowed in CDATA and it appears in jquery!
            # Try to prevent that..
            javascript = resource_string(*args).replace("']]>'", "']' + ']>'")
            stag = '<script type="text/javascript"><![CDATA[\n%s\n]]></script>'
            
            return stag % javascript
        
        javascript_text = SCRIPT_TAG.sub(match, javascript_text)
                                          
        self.full_svg_document.appendChild(self.svg)
        self.full_svg_document.appendChild(RawNode(javascript_text))
        self.svg = self.full_svg_document
        result = super(NavigableSVGDocument, self).toprettyxml()
        return result