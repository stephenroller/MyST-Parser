"""A post-transform for overriding the behaviour of sphinx reference resolution.

This is applied to MyST type references only, such as ``[text](target)``,
and allows for nested syntax
"""
import os
from typing import Any, List, Tuple
from typing import cast

from docutils import nodes
from docutils.nodes import document, Element

from sphinx import addnodes
from sphinx.addnodes import pending_xref
from sphinx.locale import __
from sphinx.transforms.post_transforms import ReferencesResolver
from sphinx.util import docname_join, logging
from sphinx.util.nodes import clean_astext, make_refnode

try:
    from sphinx.errors import NoUri
except ImportError:
    # sphinx < 2.1
    from sphinx.environment import NoUri

logger = logging.getLogger(__name__)


class MystReferenceResolver(ReferencesResolver):
    """Resolves cross-references on doctrees.

    Overrides default sphinx implementation, to allow for nested syntax
    """

    default_priority = 9  # higher priority than ReferencesResolver (10)

    def run(self, **kwargs: Any) -> None:
        self.document: document
        for node in self.document.traverse(addnodes.pending_xref):
            if node["reftype"] != "myst":
                continue

            contnode = cast(nodes.TextElement, node[0].deepcopy())
            newnode = None

            typ = node["reftype"]
            target = node["reftarget"]
            refdoc = node.get("refdoc", self.env.docname)
            domain = None

            try:
                newnode = self.resolve_myst_ref(refdoc, node, contnode)
                if newnode is None:
                    # no new node found? try the missing-reference event
                    # but first we change the the reftype to 'any'
                    # this means it is picked up by extensions like intersphinx
                    node["reftype"] = "any"
                    newnode = self.app.emit_firstresult(
                        "missing-reference", self.env, node, contnode
                    )
                    node["reftype"] = "myst"
                    # still not found? warn if node wishes to be warned about or
                    # we are in nit-picky mode
                    if newnode is None:
                        node["refdomain"] = ""
                        self.warn_missing_reference(refdoc, typ, target, node, domain)
            except NoUri:
                newnode = contnode

            node.replace_self(newnode or contnode)

    def _resolve_ref_nested(self, node: pending_xref, fromdocname: str) -> Element:
        """This is the same as ``sphinx.domains.std._resolve_ref_xref``,
        but allows for nested syntax,
        rather than converting the inner nodes to raw text.
        """
        stddomain = self.env.get_domain("std")
        target = node["reftarget"].lower()

        if node["refexplicit"]:
            # reference to anonymous label; the reference uses
            # the supplied link caption
            docname, labelid = stddomain.anonlabels.get(target, ("", ""))
            sectname = node.astext()
            innernode = nodes.inline(sectname, "")
            innernode.extend(node[0].children)
        else:
            # reference to named label; the final node will
            # contain the section name after the label
            docname, labelid, sectname = stddomain.labels.get(target, ("", "", ""))
            innernode = nodes.inline(sectname, sectname)

        if not docname:
            return None

        return make_refnode(self.app.builder, fromdocname, docname, labelid, innernode)

    def _resolve_doc_nested(self, node: pending_xref, fromdocname: str) -> Element:
        """This is the same as ``sphinx.domains.std._resolve_doc_xref``,
        but allows for nested syntax,
        rather than converting the inner nodes to raw text.

        It also allows for extensions on document names.
        """
        # directly reference to document by source name; can be absolute or relative
        refdoc = node.get("refdoc", fromdocname)
        docname = docname_join(refdoc, node["reftarget"])

        if docname not in self.env.all_docs:
            # try stripping known extensions from doc name
            if os.path.splitext(docname)[1] in self.env.config.source_suffix:
                docname = os.path.splitext(docname)[0]
            if docname not in self.env.all_docs:
                return None

        if node["refexplicit"]:
            # reference with explicit title
            caption = node.astext()
            innernode = nodes.inline(caption, "", classes=["doc"])
            innernode.extend(node[0].children)
        else:
            # TODO do we want nested syntax for titles?
            caption = clean_astext(self.env.titles[docname])
            innernode = nodes.inline(caption, caption, classes=["doc"])

        return make_refnode(self.app.builder, fromdocname, docname, None, innernode)

    def resolve_myst_ref(
        self, refdoc: str, node: pending_xref, contnode: Element
    ) -> Element:
        """Resolve reference generated by the "myst" role."""

        stddomain = self.env.get_domain("std")
        target = node["reftarget"]
        results = []  # type: List[Tuple[str, Element]]

        # resolve standard references first
        res = self._resolve_ref_nested(node, refdoc)
        if res:
            results.append(("std:ref", res))

        # next resolve doc names
        res = self._resolve_doc_nested(node, refdoc)
        if res:
            results.append(("std:doc", res))

        # next resolve for any other standard reference object
        for objtype in stddomain.object_types:
            key = (objtype, target)
            if objtype == "term":
                key = (objtype, target.lower())
            if key in stddomain.objects:
                docname, labelid = stddomain.objects[key]
                domain_role = "std:" + stddomain.role_for_objtype(objtype)
                ref_node = make_refnode(
                    self.app.builder, refdoc, docname, labelid, contnode
                )
                results.append((domain_role, ref_node))

        # finally resolve for any other type of reference
        # TODO do we want to restrict this?
        for domain in self.env.domains.values():
            if domain.name == "std":
                continue  # we did this one already
            try:
                results.extend(
                    domain.resolve_any_xref(
                        self.env, refdoc, self.app.builder, target, node, contnode
                    )
                )
            except NotImplementedError:
                # the domain doesn't yet support the new interface
                # we have to manually collect possible references (SLOW)
                for role in domain.roles:
                    res = domain.resolve_xref(
                        self.env, refdoc, self.app.builder, role, target, node, contnode
                    )
                    if res and isinstance(res[0], nodes.Element):
                        results.append((f"{domain.name}:{role}", res))

        # now, see how many matches we got...
        if not results:
            return None
        if len(results) > 1:

            def stringify(name, node):
                reftitle = node.get("reftitle", node.astext())
                return f":{name}:`{reftitle}`"

            candidates = " or ".join(stringify(name, role) for name, role in results)
            logger.warning(
                __(
                    f"more than one target found for 'myst' cross-reference {target}: "
                    f"could be {candidates}"
                ),
                location=node,
            )

        res_role, newnode = results[0]
        # Override "myst" class with the actual role type to get the styling
        # approximately correct.
        res_domain = res_role.split(":")[0]
        if len(newnode) > 0 and isinstance(newnode[0], nodes.Element):
            newnode[0]["classes"] = newnode[0].get("classes", []) + [
                res_domain,
                res_role.replace(":", "-"),
            ]

        return newnode
