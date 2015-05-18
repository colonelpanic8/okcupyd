from okcupyd_testing.util import *
okcupyd_vcr.cassette_library_dir = os.path.join(
    os.path.dirname(__file__), 'vcr_cassettes'
)
