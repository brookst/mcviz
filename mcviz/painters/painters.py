from os.path import basename

from ..svg import SVGDocument
from ..svg import identity, photon, final_photon, gluon, multigluon, boson, fermion, hadron, vertex
from ..layouts import get_layout
from ..styles import apply_style
from ..graphviz import run_graphviz



from logging import getLogger; log = getLogger("painter")

class Painter(object):
    def __init__(self, graph_view, output_file, options):
        self.graph = graph_view
        self.output_file = output_file
        self.options = options
        self.extension = basename(output_file).split(".")[-1]

    def layout(self):
        # Get the specified layout class and create a layout of the graph
        layout_class = get_layout(self.options.layout)
        self.layout = layout_class(self.graph, self.options)

    def style(self):
        # Apply any specified styles onto the layouted graph
        for style in self.options.style:

            log.debug('applying style: %s' % style)
            apply_style(style, self.layout)
            print self.layout.edges[0].style_args

    def write_data(self, data_string):
        # Dump the data to stdout if required
        if self.output_file == "-":
            print data_string
        else:
            # Write the data to file otherwise
            with open(self.output_file, "w") as f:
                f.write(data_string)

    def recalculate_boundingbox(self):
        # if we do not know the scale; (i.e. bounding box) calculate it
        x_min, y_min, x_max, y_max = 0, 0, 0, 0
        def get_minmax(x,y):
            return min(x, x_min), min(y, y_min), max(x, x_max), max(y, y_max)

        for edge in self.layout.edges:
            if edge.spline:
                x0, x1, y0, y1 = edge.spline.boundingbox
                x_min, y_min, x_max, y_max = get_minmax(x0, y0)
                x_min, y_min, x_max, y_max = get_minmax(x1, y0)
                x_min, y_min, x_max, y_max = get_minmax(x0, y1)
                x_min, y_min, x_max, y_max = get_minmax(x1, y1)

        for node in self.layout.nodes:
            if node.center:
                x_min, y_min, x_max, y_max = get_minmax(node.center.x, node.center.y)
        wx = x_max - x_min
        wy = y_max - y_min
        if not self.layout.width:
            self.layout.width = 100
            self.layout.height = 100
            self.layout.scale = 1
        else:
            self.layout.scale = min(self.width/wx, self.height/wy)

class GraphvizPainter(Painter):
    def graphviz_pass(self, engine, graphviz_options, dot_data):
        # Dump the whole dot file before passing it to graphviz if requested
        if self.options.dump_dot:
            log.debug("Data passed to %s:\n%s" % (engine, dot_data))

        # Process the DOT data with graphviz
        log.debug("Calling '%s' with options %s" % (engine, graphviz_options))
        output, errors = run_graphviz(engine, dot_data, graphviz_options)
        errors = map(str.strip, errors.split("\n"))
        errors = filter(lambda e : e and not "Warning: gvrender" in e, errors)
        if errors:
            log.warning("********* GraphViz Output **********")
            for error in errors:
                log.warning(error)
            log.warning("************************************")
        if not output.strip():
            log.error("No output from %s " % engine)
            log.error("There may be too many constraints on the graph.")
        return output

    def paint(self):
        self.layout()
        self.style()
        engine = self.options.layout_engine
        engine = engine if engine else "dot"
        opts = self.options.extra_gv_options
        if not any(opt.startswith("-T") for opt in opts):
            opts.append("-T%s" % self.extension)
        self.write_data(self.graphviz_pass(engine, opts, self.layout.dot))
    

class SVGPainter(GraphvizPainter):

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

    def paint(self):
        self.layout()
        apply_style("svg", self.layout)
        self.style()
        engine = self.options.layout_engine
        engine = engine if engine else "dot"
        opts = self.options.extra_gv_options
        if not any(opt.startswith("-T") for opt in opts):
            opts.append("-Tplain")
        assert "-Tplain" in opts, "For SVG painting with the internal painter only -Tplain is supported"
        plain = self.graphviz_pass(engine, opts, self.layout.dot)
        self.layout.update_from_plain(plain)
    
        self.doc = SVGDocument(self.layout.width, self.layout.height, self.layout.scale)
        for edge in self.layout.edges:
            if not edge.spline:
                # Nothing to paint!
                continue
            self.paint_edge(edge)
        for node in self.layout.nodes:
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
            if "<" in edge.label:
                self.doc.add_glyph(edge.item.pdgid, edge.label_center,
                               self.options.label_size,
                               ", ".join(map(str, edge.item.subscripts)))
            else:
                self.doc.add_text_glyph(edge.label, edge.label_center,
                               self.options.label_size,
                               ", ".join(map(str, edge.item.subscripts)))


    def paint_vertex(self, node):
        if node.show and node.center:
            vx = vertex(node.center, node.width/2, node.height/2,
                        **node.style_args)
            self.doc.add_object(vx)
           
        if node.label and node.center:
            # This needs fixing for the Feynman layout, if we want node labels.
            self.doc.add_glyph(node.item.pdgid, node.center.tuple(),
                               self.options.label_size,
                               ", ".join(map(str, node.item.subscripts)))

class DOTPainter(Painter):
    def paint(self):
        self.layout()
        self.style()
        self.write_data(self.layout.dot)

