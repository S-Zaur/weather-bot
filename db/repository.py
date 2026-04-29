from db import dao


class Repository:
    def __init__(self, session):
        self.session = session
        self.state = dao.StateDAO(session)
        self.user = dao.UserDAO(session)
        self.location = dao.LocationDAO(session)
