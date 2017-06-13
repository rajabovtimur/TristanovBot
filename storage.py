import json, datetime

class DataStore(object):
    def __init__(self):
        self.labfile = None
        self.schedulefile = None
        self.userfile = None
        self.groupdata = None
        self.labdata = None
        self.scheduledata = None
        self.userdata = None

    def dassert(self):
        if self.labfile is None or self.schedulefile is None or self.userfile is None:
            raise Exception("not initialized")

    def set_labfile(self, path):
        self.labfile = path
        with open(path) as fl:
            lines = fl.readlines()
            content = ''.join(lines)
            self.labdata = json.loads(content)

    def set_schedulefile(self, path):
        self.schedulefile = path
        with open(path) as fl:
            lines = fl.readlines()
            content = ''.join(lines)
            self.scheduledata = json.loads(content)

    def set_groupfile(self, path):
        with open(path) as fl:
            lines = fl.readlines()
            content = ''.join(lines)
            self.groupdata = json.loads(content)

    def set_userinfofile(self, path):
        self.userfile = path
        with open(path) as fl:
            lines = fl.readlines()
            content = ''.join(lines)
            parsed = json.loads(content)
            self.userdata = {}
            for p in parsed:
                self.userdata[p["id"]] = {
                    "group": p.get("group", None),
                    "state": p.get('state', None)
                }

    def set_user_group(self, user, group):
        dt = self.userdata.get(user, {})
        dt['group'] = group
        self.userdata[user] = dt
        content = []
        for k,v in self.userdata.iteritems():
            content.append({
                "id": k,
                "group": v.get("group", None),
                "state": v.get("state", None)
            })
        with open(self.userfile, "w+") as fl:
            fl.write( json.dumps(content, indent=2) )
            fl.flush()

    def get_user_group(self, user):
        data = self.userdata.get(user, None)
        if data is None:
            return None
        return data["group"]

    def set_user_state(self, user, state):
        dt = self.userdata.get(user, {})
        print dt, user
        dt['state'] = state
        self.set_user_group(user, dt['group'])

    def get_user_state(self, user):
        data = self.userdata.get(user, None)
        if data is None:
            return None
        return data["state"]

    def groups(self):
        self.dassert()
        return self.groupdata

    def schedule_byday(self, group, day):
        '''
        day - 0..5 [Mon..Sat]
        '''
        self.dassert()
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        for item in self.scheduledata:
            if item["group"].lower() == group.lower():
                for itemday in item["days"]:
                    if itemday["day"] == days[day]:
                        return itemday["schedule"]
        return []

    def schedule_bydate(self, group, day):
        self.dassert()
        return self.schedule_byday(group, day.weekday())

    def schedule_lab_disciplines(self, group):
        self.dassert()
        for item in self.labdata:
            if item["group"].lower() == group.lower():
                disciplines = []
                for x in item["labs"]:
                    disciplines.append(x["discipline"])
                return disciplines
        return []

    def schedule_labs_bydiscipline(self, group, discipline):
        self.dassert()
        for item in self.labdata:
            if item["group"].lower() == group.lower():
                for x in item["labs"]:
                    if x["discipline"].lower() == discipline:
                        return x["labs"]
        return []