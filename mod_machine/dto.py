
class MailDTO:
    def __init__(self, max_cpu, max_men, max_disc, current_men, current_cpu, current_disc):
        self.max_cpu = max_cpu
        self.max_men = max_men
        self.max_disc = max_disc
        self.current_men = current_men
        self.current_cpu = current_cpu
        self.current_disc = current_disc