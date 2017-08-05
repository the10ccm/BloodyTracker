
class ParsingError(ValueError):
    """Exception raised for errors over timesheet editing """
    def __init__(self, msg, lnum):
        self.msg = msg
        self.lnum = lnum
