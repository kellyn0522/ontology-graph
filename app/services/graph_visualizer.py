from pyvis.network import Network


class GraphVisualizer:

    def __init__(
        self, 
        core_classes: list = None
    ):
        
        self.core_classes = set(
            core_classes or []
        )

        self.net = Network(
            height="950px",
            width="100%",
            bgcolor="#F8FAFC",
            font_color="#2C3E50",
            directed=True
        )

        # ---------------------------------------------------
        # 안정적인 Physics
        # ---------------------------------------------------

        self.net.set_options("""
        {
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",

            "forceAtlas2Based": {
              "gravitationalConstant": -45,
              "centralGravity": 0.01,
              "springLength": 180,
              "springConstant": 0.03,
              "damping": 0.9
            },

            "minVelocity": 0.75
          },

          "edges": {
            "smooth": {
              "type": "dynamic"
            }
          }
        }
        """)

    # ---------------------------------------------------
    # CLASS NODE
    # ---------------------------------------------------

    def _add_class_node(
        self,
        node_name: str
    ):

        # ---------------------------------------------------
        # CENTRAL HUB
        # ---------------------------------------------------

        if node_name in self.core_classes:

            self.net.add_node(
                node_name,

                label=node_name,

                shape="dot",

                size=38,

                color={
                    "background": "#FFF3B0",
                    "border": "#F4A261",

                    "highlight": {
                        "background": "#FFE599",
                        "border": "#E76F51"
                    }
                },

                borderWidth=4,

                font={
                    "size": 24,
                    "color": "#5C3D00",
                    "face": "arial"
                },

                shadow={
                    "enabled": True,
                    "color": "rgba(244,162,97,0.25)",
                    "size": 18,
                    "x": 0,
                    "y": 0
                }
            )

        # ---------------------------------------------------
        # NORMAL NODE
        # ---------------------------------------------------

        else:

            self.net.add_node(
                node_name,

                label=node_name,

                shape="dot",

                size=22,

                color={
                    "background": "#D8F3DC",
                    "border": "#52B788",

                    "highlight": {
                        "background": "#B7E4C7",
                        "border": "#40916C"
                    }
                },

                borderWidth=3,

                font={
                    "size": 18,
                    "color": "#1B4332",
                    "face": "arial"
                },

                shadow={
                    "enabled": True,
                    "color": "rgba(82,183,136,0.18)",
                    "size": 10,
                    "x": 0,
                    "y": 0
                }
            )

    # ---------------------------------------------------
    # BUILD GRAPH
    # ---------------------------------------------------

    def build(
        self,
        ontology_data: dict,
        allowed_relations: list = None
    ):

        added_nodes = set()

        hierarchies = ontology_data.get(
            "refined_hierarchies",
            []
        )

        relations = ontology_data.get(
            "refined_relations",
            []
        )

        # ---------------------------------------------------
        # HIERARCHY
        # ---------------------------------------------------

        for hierarchy in hierarchies:

            parent = hierarchy["parent"]

            child = hierarchy["child"]

            relation = hierarchy["relation"]

            # relation filtering
            if allowed_relations:

                if relation not in allowed_relations:
                    continue

            # Parent Node
            if parent not in added_nodes:

                self._add_class_node(parent)

                added_nodes.add(parent)

            # Child Node
            if child not in added_nodes:

                self._add_class_node(child)

                added_nodes.add(child)

            # Edge
            self.net.add_edge(
                child,
                parent,

                label="subClassOf",

                color={
                    "color": "#F4A261",
                    "highlight": "#E76F51",
                    "hover": "#E76F51"
                },

                width=3.5,

                arrows="to",

                font={
                    "size": 16,
                    "color": "#E76F51",
                    "face": "arial"
                }
            )

        # ---------------------------------------------------
        # SEMANTIC RELATION
        # ---------------------------------------------------

        for rel in relations:

            subject = rel["subject"]

            predicate = rel["predicate"]

            object_ = rel["object"]

            # relation filtering
            if allowed_relations:

                if predicate not in allowed_relations:
                    continue

            # Subject Node
            if subject not in added_nodes:

                self._add_class_node(subject)

                added_nodes.add(subject)

            # Object Node
            if object_ not in added_nodes:

                self._add_class_node(object_)

                added_nodes.add(object_)

            # ---------------------------------------------------
            # EDGE COLOR
            # ---------------------------------------------------

            edge_color = "#F4A261"

            if predicate == "requires":
                edge_color = "#E63946"

            elif predicate == "belongsTo":
                edge_color = "#457B9D"

            elif predicate == "manages":
                edge_color = "#2A9D8F"

            elif predicate == "includes":
                edge_color = "#F4A261"

            elif predicate == "subscribesTo":
                edge_color = "#9B5DE5"

            # ---------------------------------------------------
            # EDGE
            # ---------------------------------------------------

            self.net.add_edge(
                subject,
                object_,

                label=predicate,

                color={
                    "color": edge_color,
                    "highlight": edge_color,
                    "hover": edge_color
                },

                width=2.5,

                arrows="to",

                font={
                    "size": 15,
                    "color": edge_color,
                    "face": "arial"
                }
            )

    # ---------------------------------------------------
    # SAVE
    # ---------------------------------------------------

    def save(
        self,
        output_path: str
    ):

        self.net.write_html(
            output_path,
            notebook=False
        )
