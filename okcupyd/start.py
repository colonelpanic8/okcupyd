from okcupyd import *


session = Session.login()
af = AttractivenessFinder()
u = User(session)
PhotoUploader = PhotoUploader(session=session)
