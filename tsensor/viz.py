import sys
import tempfile
import graphviz
import token
from IPython.display import SVG
import matplotlib.patches as patches
import matplotlib.pyplot as plt

import tsensor
import tsensor.ast
import tsensor.analysis
import tsensor.parsing


def pyviz(statement:str, frame=None,
          fontsize=16,
          fontname='Consolas',
          matrixcolor="#cfe2d4", vectorcolor="#fefecd",
          char_sep_scale=2.5,
          ax=None,
          figsize=None):
    if frame is None: # use frame of caller if not passed in
        frame = sys._getframe().f_back
    root, tokens = tsensor.parsing.parse(statement)
    root.eval(frame)
    subexprs = tsensor.analysis.smallest_matrix_subexpr(root)

    print(statement)
    for i in range(8):
        for j in range(10):
            print(j,end='')
    print()
    for sub in subexprs:
        print(sub, sub.start.start_idx, ':', sub.stop.stop_idx)

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # space_w, _ = textdim(' ', fontname=fontname, fontsize=fontsize)

    # width of any char for fixed-width font
    w, _ = textdim(' ', fontname=fontname, fontsize=fontsize)
    print("wid",w)

    w *= char_sep_scale
    # w = 2*fontsize
    x = 0
    # for tok in tokens:
    #     ax.text(x, 0, tok.value, fontname=fontname, fontsize=fontsize)
    #     w, h = textdim(tok.value, fontname=fontname, fontsize=fontsize)
    #     print(tok.value, w, h)
    #     x = x + w + space_w
    #     print(x)
    for c in statement:
        ax.text(x, 0, c, fontname=fontname, fontsize=fontsize)
        # w, h = textdim(c, fontname=fontname, fontsize=fontsize)
        x = x + w

    ax.set_xlim(0, len(statement)*w)
    # ax.set_ylim(30)
    fig.set_size_inches(x/200,70/200)

    ax.axis("off")


def textdim(s, fontname='Consolas', fontsize=11):
    fig, ax = plt.subplots(1, 1)
    t = ax.text(0, 0, s, fontname=fontname, fontsize=fontsize)
    bb = t.get_window_extent(find_renderer(fig))
    print(s, bb.width, bb.height)

    # t = mpl.textpath.TextPath(xy=(0, 0), s=s, size=fontsize, prop=fontname)
    # bb = t.get_extents()
    # print(s, "new", bb)
    plt.close()
    return bb.width, bb.height

# From: https://stackoverflow.com/questions/22667224/matplotlib-get-text-bounding-box-independent-of-backend
def find_renderer(fig):
    if hasattr(fig.canvas, "get_renderer"):
        #Some backends, such as TkAgg, have the get_renderer method, which
        #makes this easy.
        renderer = fig.canvas.get_renderer()
    else:
        #Other backends do not have the get_renderer method, so we have a work
        #around to find the renderer.  Print the figure to a temporary file
        #object, and then grab the renderer that was used.
        #(I stole this trick from the matplotlib backend_bases.py
        #print_figure() method.)
        import io
        fig.canvas.print_pdf(io.BytesIO())
        renderer = fig._cachedRenderer
    return(renderer)


# ----------------

class QuietGraphvizWrapper(graphviz.Source):
    def __init__(self, dotsrc):
        super().__init__(source=dotsrc)

    def _repr_svg_(self):
        return self.pipe(format='svg', quiet=True).decode(self._encoding)
def pyviz_old(statement:str, frame=None) -> graphviz.Source:
    if frame is None: # use frame of caller
        frame = sys._getframe().f_back
    return QuietGraphvizWrapper(pyviz_dot(statement, frame))

def pyviz_dot(statement:str, frame,
              matrixcolor="#cfe2d4", vectorcolor="#fefecd",
              gtype="digraph", gname="G") -> str:

    def elem_label(token_or_node):
        x = tok2node[token_or_node] if token_or_node in tok2node else token_or_node
        sh = tsensor.analysis._shape(x.value) # get value for this node in tree
        label = f'<font face="{fontname}" color="#444443" point-size="{fontsize}">{token_or_node}</font>'
        if sh is not None:
            if len(sh) == 1:
                label = matrix_html(sh[0], None, token_or_node.value, fontname=fontname,
                                    fontsize=fontsize, color=vectorcolor)
            elif len(sh) == 2:
                label = matrix_html(sh[0], sh[1], token_or_node.value, fontname=fontname,
                                    fontsize=fontsize, color=matrixcolor)
        # print(x,'has',sh,label)
        return label

    def internal_label(node):
        text = str(node)
        if node.opstr:
            text = node.opstr
        sh = tsensor.ast._shape(node.value) # get value for this node in tree
        label = f'<font face="{fontname}" color="#444443" point-size="{fontsize}">{text}</font>'
        if sh is not None:
            if len(sh) == 1:
                label = matrix_html(sh[0], None, text, fontname=fontname,
                                    fontsize=fontsize, color=vectorcolor)
            elif len(sh) == 2:
                label = matrix_html(sh[0], sh[1], text, fontname=fontname,
                                    fontsize=fontsize, color=matrixcolor)
        # print(x,'has',sh,label)
        return label

    root, tokens = tsensor.parsing.parse(statement)
    root.eval(frame)
    result = root.value

    # p = tsensor.parsing.PyExprParser(statement)
    # root = p.parse()
    # print(root)
    # print(repr(root))
    nodes = tsensor.ast.postorder(root)
    atoms = tsensor.ast.leaves(root)
    atomsS = set(atoms)
    ops = [nd for nd in nodes if nd not in atomsS] # keep order

    # result = root.eval(frame)

    # ignore = set()
    # def foo(t):
    #     # print("walk", t, repr(t), tsensor.analysis._shape(t.value))
    #     if isinstance(t,tsensor.ast.Member):
    #         if tsensor.analysis._shape(t.obj.value) is None:
    #             # print("\tignore", t)
    #             ignore.add(t)
    #     else:
    #         if tsensor.analysis._shape(t.value) is None:
    #             # print("\tignore", t)
    #             ignore.add(t)
    # tsensor.ast.walk(root, post=foo)
    # print("ignore",[str(n) for n in ignore])
    #
    # map tokens to nodes so we can get variable values
    tok2node = {nd.token:nd for nd in atoms}
    # print(tok2node)

    gr = gtype+" "+gname+""" {
        margin=0;
        nodesep=.01;
        ranksep=.3;
        rankdir=BT;
        ordering=out; # keep order of leaves
    """

    fontname="Consolas"
    fontsize=12
    spread = 0

    # Gen leaf nodes
    for i in range(len(tokens)):
        t = tokens[i]
        if t.type!=token.ENDMARKER:
            label = elem_label(t)
            _spread = spread
            if t.type==token.DOT:
                _spread=.1
            elif t.type==token.EQUAL:
                _spread=.25
            elif t.type in tsensor.parsing.ADDOP:
                _spread=.4
            elif t.type in tsensor.parsing.MULOP:
                _spread=.2
            gr += f'leaf{id(t)} [shape=box penwidth=0 margin=.001 width={_spread} label=<{label}>]\n'

    # Make sure leaves are on same level
    gr += f'{{ rank=same; '
    for t in tokens:
        if t.type!=token.ENDMARKER:
            gr += f' leaf{id(t)}'
    gr += '\n}\n'

    # Make sure leaves are left to right by linking
    for i in range(len(tokens) - 2):
        t = tokens[i]
        t2 = tokens[i + 1]
        gr += f'leaf{id(t)} -> leaf{id(t2)} [style=invis];\n'

    # # Draw internal ops nodes
    # for nd in ops:
    #     # x = tok2node[t] if t in tok2node else t
    #     # if isinstance(nd, tsensor.ast.Member):
    #     #     continue
    #     for sub in nd.kids:
    #         if tsensor.ast._shape(sub.value) is None:
    #             continue
    #     label = internal_label(nd)
    #     gr += f'node{id(nd)} [shape=box penwidth=0 margin=0 height=.3 label=<{label}>]\n'
    #     # gr += f'node{id(nd)} [shape=box penwidth=0 height=.3 margin=0 label=<<font face="Consolas" color="#444443" point-size="12">{nd}</font>>]\n'
    #
    # # Link internal nodes to other nodes or leaves
    # for nd in nodes:
    #     kids = nd.kids
    #     # if isinstance(nd, tsensor.ast.Member) and tsensor.ast._shape(nd.obj) is None:
    #     #     continue
    #     # if isinstance(nd, tsensor.ast.Call) and isinstance(nd.kids[0], tsensor.ast.Member):
    #     #     print('ignore', nd.func, kids)
    #     #     kids = kids[1:]
    #     for sub in kids:
    #         if sub in atomsS:
    #             gr += f'node{id(nd)} -> leaf{id(sub.token)} [dir=back, penwidth="0.5", color="#444443", arrowsize=.4];\n'
    #         else:
    #             gr += f'node{id(nd)} -> node{id(sub)} [dir=back, penwidth="0.5", color="#444443", arrowsize=.4];\n'

    gr += "}\n"
    return gr


def astviz(statement:str, frame=None) -> graphviz.Source:
    return QuietGraphvizWrapper(astviz_dot(statement, frame))


def astviz_dot(statement:str, frame=None) -> str:
    def internal_label(node):
        text = str(node)
        if node.opstr:
            text = node.opstr
        sh = tsensor.analysis._shape(node.value)
        if sh is None:
            return f'<font face="{fontname}" color="#444443" point-size="{fontsize}">{text}</font>'

        if len(sh)==1:
            sz = str(sh[0])
        else:
            sz = f"{sh[0]}x{sh[1]}"
        return f"""<font face="Consolas" color="#444443" point-size="{fontsize}">{text}</font><br/><font face="Consolas" color="#444443" point-size="{dimfontsize}">{sz}</font>"""

    root, tokens = tsensor.parsing.parse(statement)
    if frame is not None:
        root.eval(frame)

    nodes = tsensor.ast.postorder(root)
    atoms = tsensor.ast.leaves(root)
    atomsS = set(atoms)
    ops = [nd for nd in nodes if nd not in atomsS] # keep order
    # map tokens to nodes so we can get variable values
    tok2node = {nd.token:nd for nd in atoms}

    gr = """digraph G {
        margin=0;
        nodesep=.01;
        ranksep=.3;
        rankdir=BT;
        ordering=out; # keep order of leaves
    """

    matrixcolor = "#cfe2d4"
    vectorcolor = "#fefecd"
    fontname="Consolas"
    fontsize=12
    dimfontsize = 9
    spread = 0

    # Gen leaf nodes
    for i in range(len(tokens)):
        t = tokens[i]
        if t.type!=token.ENDMARKER:
            nodetext = t.value
            label = f'<font face="{fontname}" color="#444443" point-size="{fontsize}">{nodetext}</font>'
            _spread = spread
            if t.type==token.DOT:
                _spread=.1
            elif t.type==token.EQUAL:
                _spread=.25
            elif t.type in tsensor.parsing.ADDOP:
                _spread=.4
            elif t.type in tsensor.parsing.MULOP:
                _spread=.2
            gr += f'leaf{id(t)} [shape=box penwidth=0 margin=.001 width={_spread} label=<{label}>]\n'

    # Make sure leaves are on same level
    gr += f'{{ rank=same; '
    for t in tokens:
        if t.type!=token.ENDMARKER:
            gr += f' leaf{id(t)}'
    gr += '\n}\n'

    # Make sure leaves are left to right by linking
    for i in range(len(tokens) - 2):
        t = tokens[i]
        t2 = tokens[i + 1]
        gr += f'leaf{id(t)} -> leaf{id(t2)} [style=invis];\n'

    # Draw internal ops nodes
    for nd in ops:
        # for sub in nd.kids:
        #     if tsensor.analysis._shape(sub.value) is None:
        #         continue
        label = internal_label(nd)
        sh = tsensor.analysis._shape(nd.value)
        if sh is None:
            color = ""
        else:
            if len(sh)==1:
                color = f'fillcolor="{vectorcolor}" style=filled'
            else:
                color = f'fillcolor="{matrixcolor}" style=filled'
        gr += f'node{id(nd)} [shape=box {color} penwidth=0 margin=0 width=.25 height=.2 label=<{label}>]\n'

    # Link internal nodes to other nodes or leaves
    for nd in nodes:
        kids = nd.kids
        for sub in kids:
            if sub in atomsS:
                gr += f'node{id(nd)} -> leaf{id(sub.token)} [dir=back, penwidth="0.5", color="#6B6B6B", arrowsize=.3];\n'
            else:
                gr += f'node{id(nd)} -> node{id(sub)} [dir=back, penwidth="0.5", color="#6B6B6B", arrowsize=.3];\n'

    gr += "}\n"
    return gr


def matrix_html(nrows, ncols, label, fontsize=12, fontname="Consolas", dimfontsize=9, color="#cfe2d4"):
    isvec = ncols==None
    if isvec:
        sz = str(nrows)
        ncols=nrows
        nrows=1
    else:
        sz = f"{nrows}x{ncols}"
    w = ncols*20
    h = nrows*20
    if ncols==1:
        w = 15
    if nrows==1:
        h = 15
    html = f"""
    <table fixedsize="true" width="{w}" height="{h+2*fontsize*1.1}" BORDER="0" CELLPADDING="0" CELLBORDER="1" CELLSPACING="0">
    <tr>
    <td fixedsize="true" width="{w}" height="{fontsize*1.1}" cellspacing="0" cellpadding="0" border="0" valign="bottom" align="center">
    <font face="{fontname}" color="#444443" point-size="{dimfontsize}">{sz}</font>
    </td>
    </tr>
    <tr>    
    <td fixedsize="true" width="{w}" height="{h}" cellspacing="0" cellpadding="0" bgcolor="{color}" border="1" sides="ltbr" align="center">
    <font face="{fontname}" color="#444443" point-size="{fontsize}">{label}</font>
    </td>
    </tr>
    </table>"""
    return html


