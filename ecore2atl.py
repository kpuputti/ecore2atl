"""\
ecore2atl.py - Convert ecore files into atl.
Author: Kimmo Puputti (kpuputti at gmail)

Usage: python ecore2atl.py path/to/file.ecore model_name

All the ecore:EClass elements are parsed into separate rules and saved
into a file ${model_name}.atl. The resulting atl file is just a
collection for dummy rules that copy all the attributes of the input
models into the output models.

The output can then be extended to provide more interesting rules
between the input and output models. This way the refining-mode of atl
can be avoided (as that was the reason for developing this script in
the first place).

Note that the output is not a one-to-one mapping of the input. The
output is intended to be used as a base for extending the rules by
hand.
"""
from xml.dom import minidom
import sys


# Whitespace to use for indentation.
INDENT = ' ' * 4


class Rule(object):
    """Represents an atl rule that has a list of attributes."""

    def __init__(self, name, ns):
        self.name = name
        self.ns = ns
        self.attrs = []

    def add_attr(self, attr):
        self.attrs.append(attr)

    def __str__(self):
        rtype = '%s!%s' % (self.ns, self.name)
        lines = [
            'rule %sRule {' % (self.name),
            '%sfrom' % (INDENT),
            '%sc_in: %s' % (INDENT * 2, rtype),
            '%sto' % (INDENT),
            '%sc_out: %s (' % (INDENT * 2, rtype),
        ]

        attrs = []
        for attr in self.attrs:
            attrs.append('%s%s <- c_in.%s' % (INDENT * 3, attr, attr))
        lines.append(',\n'.join(attrs))

        lines.append('%s)' % (INDENT * 2))
        lines.append('}')
        return '\n'.join(lines)


def get_rule(classifier, ns_prefix):
    """Return a Rule instance parsed from the given node."""
    name = classifier.attributes['name'].value
    rule = Rule(name, ns_prefix)

    for child in classifier.childNodes:
        # Skip uninteresting elements.
        if not child or child.nodeType != child.ELEMENT_NODE:
            continue
        # Add the `name' attribute values of each
        # `eStructuralFeatures' element to the attributes of the rule.
        if child.tagName == 'eStructuralFeatures':
            attr_name = child.attributes['name'].value
            rule.add_attr(attr_name)
    # Don't return rules that have no attributes.
    if not rule.attrs:
        rule = None
    return rule


def parse_rules(doc, ns_prefix):
    """Generator to yield instances of the Rule class.

    Rule class instances are parsed from the doc. Only `eClassifiers'
    tags with xsi:type `ecore:EClass' are considered.
    """
    for i, child in enumerate(doc.documentElement.childNodes):
        # Skip uninteresting elements.
        if not child or child.nodeType != child.ELEMENT_NODE:
            continue
        # Skip elements of wrong type.
        xsi_type = child.attributes['xsi:type'].value
        if child.tagName != 'eClassifiers' or xsi_type != 'ecore:EClass':
            continue
        # Skip abstract types.
        abstract = child.attributes.get('abstract', None)
        if abstract and abstract.value == 'true':
            continue
        yield get_rule(child, ns_prefix)


def main(ecore_file, model_name):
    doc = minidom.parse(ecore_file)
    ns_prefix = doc.documentElement.attributes['nsPrefix'].value
    rules = parse_rules(doc, ns_prefix)

    with open('%s.atl' % model_name, 'w') as out:
        out.write('module %s;\n' % model_name)
        out.write('create OUT: %s from IN: %s;\n' % (ns_prefix, ns_prefix))

        count = 0
        # Write down the rules.
        for rule in rules:
            if rule:
                count += 1
                out.write('\n%s\n' % str(rule))

        print 'Extracted %d rules.' % count

    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        sys.exit(main(args[0], args[1]))
    else:
        sys.stderr.write(__doc__)
        sys.exit(2)
