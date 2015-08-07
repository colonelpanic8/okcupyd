from . import filter
from . import magicnumbers


search_filters = filter.Filters()


class GentationFilter(search_filters.filter_class):

    def transform(gentation):
        return [
            magicnumbers.gentation_to_number.get(a_gentation.strip().lower(), a_gentation)
            for a_gentation in gentation
        ]

    descriptions = "A list of the allowable gentations of returned search results."
    types = list
    acceptable_values = magicnumbers.gentation_to_number.keys()
