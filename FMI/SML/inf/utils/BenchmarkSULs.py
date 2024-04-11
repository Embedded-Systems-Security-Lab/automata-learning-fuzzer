
class MockMqttExample:

    def __init__(self):
        self.state = 'CONCLOSED'
        self.topics = set()

    def subscribe(self, topic: str):
        if '\n' in topic or '\u0000' in topic:
            self.state = 'CONCLOSED'
            self.topics.clear()
        elif self.state != 'CONCLOSED':
            self.topics.add(topic)
            self.state = 'SUBACK'

        return self.state

    def unsubscribe(self, topic):
        if '\n' in topic or '\u0000' in topic:
            self.state = 'CONCLOSED'
            self.topics.clear()
        elif self.state != 'CONCLOSED':
            if topic in self.topics:
                self.topics.remove(topic)
            self.state = 'UNSUBACK'

        return self.state

    def connect(self):
        if self.state == 'CONCLOSED':
            self.state = 'CONNACK'
        else:
            self.topics.clear()
            self.state = 'CONCLOSED'
        return self.state

    def disconnect(self):
        self.state = 'CONCLOSED'
        self.topics.clear()
        return self.state

    def publish(self, topic):
        if '\n' in topic or '\u0000' in topic:
            self.state = 'CONCLOSED'
            self.topics.clear()
        if self.state != 'CONCLOSED':
            if topic not in self.topics:
                self.state = 'PUBACK'
            else:
                self.state = 'PUBACK_PUBACK'
        return self.state

def get_faulty_coffee_machine_MDP():
    from FMI.SML.inf.automata import Mdp, MdpState

    q0 = MdpState("q0", "init")
    q1 = MdpState("q1", "beep")
    q2 = MdpState("q2", "coffee")

    q0.transitions['but'].append((q0, 1))
    q0.transitions['coin'].append((q1, 1))
    q1.transitions['but'].append((q0, 0.1))
    q1.transitions['but'].append((q2, 0.9))
    q1.transitions['coin'].append((q1, 1))
    q2.transitions['but'].append((q0, 1))
    q2.transitions['coin'].append((q1, 1))

    mdp = Mdp(q0, [q0, q1, q2])

    return mdp
