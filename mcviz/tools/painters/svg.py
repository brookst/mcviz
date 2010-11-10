from logging import getLogger; log = getLogger("mcviz.painters.svg")

from mcviz.utils.svg import SVGDocument
from mcviz.utils.svg import identity, photon, final_photon, gluon, multigluon, boson, fermion, hadron, vertex
from mcviz.utils import timer
from mcviz.tool import FundamentalTool

from painters import StdPainter


class SVGPainter(StdPainter, FundamentalTool):
    _name = "svg"
    _global_args = ("label_size",)

    type_map = {"identity": identity,
                "photon": photon, 
                "final_photon": final_photon,
                "gluon": gluon, 
                "multigluon": multigluon, 
                "boson": boson, 
                "fermion": fermion, 
                "hadron": hadron, 
                "vertex": vertex
                }

    def __call__(self, layout):
        with timer("create the SVG document"):
            self.doc = SVGDocument(layout.width, layout.height, layout.scale)
            for edge in layout.edges:
                if not edge.spline:
                    # Nothing to paint!
                    continue
                self.paint_edge(edge)
            for node in layout.nodes:
                self.paint_vertex(node)

        self.write_data(self.doc.toprettyxml())

    def paint_edge(self, edge):
        """
        In the dual layout, paint a connection between particles
        """

        if edge.show and edge.spline:
            display_func = self.type_map.get(edge.style_line_type, hadron)
            self.doc.add_object(display_func(spline=edge.spline, **edge.style_args))

        if edge.label and edge.label_center:
            self.doc.add_glyph(edge.label, edge.label_center,
                           self.options["label_size"],
                           ", ".join(map(str, edge.item.subscripts)))


    def paint_vertex(self, node):
        if node.show and node.center:
            vx = vertex(node.center, node.width/2, node.height/2,
                        **node.style_args)
            self.doc.add_object(vx)
           
        if not node.label is None and node.center:
            self.doc.add_glyph(node.label, node.center.tuple(),
                               self.options["label_size"],
                               ", ".join(map(str, node.item.subscripts)))

