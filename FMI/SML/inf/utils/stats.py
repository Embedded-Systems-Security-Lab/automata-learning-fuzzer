
class Stats(object):

    def __init__(self):
        self.__num_queries = 0
        self.__num_submitted_queries = 0
        self.__num_letter = 0
        self.__num_submitted_letter = 0
        #self.__num_steps = 0
        self.__num_cached_queries = 0

    def __str__(self):
        return """ num_submitted_letter
        \t- number of queries= {}
        \t- number of submitted queries= {}
        \t- number of letter= {}
        \t- number of submitted letter= {}
        \t- number of submitted cached queriers= {}
        """.format(self.__num_queries,
                self.__num_submitted_queries,
                self.__num_letter,
                self.__num_submitted_letter,
                self.__num_cached_queries
                )

    @property
    def num_queries(self):
        """Number of queries triggered while infering"""
        return self.__num_queries

    @num_queries.setter
    def num_queries(self, num_queries):
        if num_queries is None:
            raise Exception("Number of query cannot be None")
        if num_queries < 0:
            raise Exception("Number of query must be > 0")

        self.__num_queries = num_queries

    @property
    def num_submitted_queries(self):
        """Number of query submited to the target"""
        return self.__num_submitted_queries

    @num_submitted_queries.setter
    def num_submitted_queries(self, num_submitted_queries):
        if num_submitted_queries is None:
            raise Exception("Number of submitted query cannot be None")
        if num_submitted_queries < 0:
            raise Exception("Number of submited query must be >= 0")

        self.__num_submitted_queries = num_submitted_queries

    @property
    def num_letter(self):
        """Number of letters triggered while infering"""
        return self.__num_letter

    @num_letter.setter
    def num_letter(self, num_letter):
        if num_letter is None:
            raise Exception("Number of letter cannot be None")
        if num_letter < 0:
            raise Exception("Number of letter must be > 0")

        self.__num_letter = num_letter


    @property
    def num_submitted_letter(self):
        """Number of letter submited to the target"""
        return self.__num_submitted_letter

    @num_submitted_letter.setter
    def num_submitted_letter(self, num_submitted_letter):
        if num_submitted_letter is None:
            raise Exception("Number of submited letter cannot be None")
        if num_submitted_letter < 0:
            raise Exception("Number of submited letter must be > 0")

        self.__num_submitted_letter = num_submitted_letter

    # @property
    # def num_steps(self):
    #     """Number of letter submited to the target"""
    #     return self.__num_steps

    # @num_steps.setter
    # def num_steps(self, num_steps):
    #     if num_steps is None:
    #         raise Exception("Number of steps cannot be None")
    #     if num_steps < 0:
    #         raise Exception("Number of submited letter must be > 0")

    #     self.__num_steps = num_steps

    @property
    def num_cached_queries(self):
        """Number of letter submited to the target"""
        return self.__num_cached_queries

    @num_cached_queries.setter
    def num_cached_queries(self, num_cached_queries):
        if num_cached_queries is None:
            raise Exception("Number of cached queries cannot be None")
        if num_cached_queries < 0:
            raise Exception("Number of cached queries must be > 0")

        self.__num_cached_queries = num_cached_queries


