class STATE(object):

    def __init__(self, pid, seed, crashes, last_new_path):
        super(STATE, self).__init__()
        self.pid = pid
        self.seed = seed
        self.crashes = crashes
        self.last_new_path = last_new_path

    def convert_state_to_dict(self):
        state = {"seed":self.seed,
                 "crashes":self.crashes,
                 "last_new_path":self.last_new_path}
        return state
