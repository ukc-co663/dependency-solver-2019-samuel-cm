import re


class Package:
    def __init__(self, data):
        self.name = data["name"]
        self.version = data["version"]
        self.identifier = "%s=%s" % (self.name, self.version)
        self.size = data["size"]
        self.depends = data.get("depends", [])
        self.conflicts = data.get("conflicts", [])

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return str(self)

    def satisfies(self, constraint):
        r = re.compile("([>=<]+)")
        c = re.split(r, constraint)
        if self.name != c[0]:
            return False
        if len(c) > 1:
            if c[1] == "=":
                return self.version == c[2]
            elif c[1] == ">=":
                return self.version >= c[2]
            elif c[1] == ">":
                return self.version > c[2]
            elif c[1] == "<=":
                return self.version <= c[2]
            elif c[1] == "<":
                return self.version < c[2]
        else:
            # any version
            return True

    def conflicts_with(self, package):
        return any([package.satisfies(x) for x in self.conflicts])
