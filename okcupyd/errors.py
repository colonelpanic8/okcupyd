class OkcupydError(Exception): pass

class AuthenticationError(OkcupydError): pass
class NoCorrespondentError(OkcupydError): pass
