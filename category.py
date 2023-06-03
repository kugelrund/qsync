abbreviation_to_name = {'ER': "Easy Run",
                        'EH': "Easy 100%",
                        'NR': "Nightmare Run",
                        'NH': "Nightmare 100%"}
name_to_abbreviation = {v: k for k, v in abbreviation_to_name.items()}


class Category:
    def __init__(self, name):
        if name in abbreviation_to_name:
            self.abbreviation = name
        else:
            self.abbreviation = name_to_abbreviation[name]

    def to_sda(self):
        return self.abbreviation

    def to_srcom(self):
        return abbreviation_to_name[self.abbreviation]

    def __str__(self):
        return self.abbreviation
