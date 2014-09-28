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


def test_text_for_many():
    tree = etree.XML("<top><container>"
                     "<element value='1'>one</element>"
                     "<element value='2'>two</element>"
                     "</container></top>")

    result = xpath.xpb.container.element.text_.apply_(tree)
    assert set(result) == set(['one', 'two'])


def test_attribute_contains():
    tree = etree.XML("<top><elem a='complete'></elem></top>")
    assert xpath.xpb.elem.attribute_contains('a', 'complet').apply_(tree) != []
