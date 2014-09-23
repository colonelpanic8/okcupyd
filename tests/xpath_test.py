from lxml import etree

from okcupyd import xpath


def test_selected_attribute():
    node = xpath.XPathNode(element='element', selected_attribute='value')
    assert node.xpath == '//element/@value'

    tree = etree.XML("<top><container><element value='1'>"
                 "</element><element value='2'></element></container></top>")
    builder = xpath.xpb.container.element.select_attribute_('value')

    assert builder.xpath == './/container//element/@value'
    assert builder.apply_(tree) == ['1', '2']

    assert xpath.xpb.element.select_attribute_('value', elem=tree) == ['1', '2']

