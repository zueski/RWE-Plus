from lingotojson import *
from menuclass import *


class LS(menu):

    def __init__(self, surface: pg.surface.Surface, data, items):
        self.menu = "LS"
        self.surface = surface
        self.btiles = data["EX2"]["extraTiles"]
        self.data = data

        self.items = items

        self.rectdata = [[0, 0], [0, 0], [0, 0]]
        self.xoffset = 0
        self.yoffset = 0

        self.size = settings["TE"]["cellsize"]

        self.message = ''

        self.ofstop = ofstop
        self.ofsleft = ofsleft

        self.field = None

        self.recount()
        self.init()
        self.blit()
        self.resize()

    def recount(self):
        self.gw = len(self.data["GE"])
        self.gh = len(self.data["GE"][0])
        self.tw = len(self.data["TE"]["tlMatrix"])
        self.th = len(self.data["TE"]["tlMatrix"][0])

        self.recount_image()

    def blit(self):
        if self.field is not None:
            self.labels[0].set_text(self.labels[0].originaltext % (self.imagew, self.imageh, self.imagewp, self.imagehp))
        else:
            self.labels[0].set_text("Image not found! try make it in light editor!")
        self.labels[1].set_text(self.labels[1].originaltext % (self.gw, self.gh))
        self.labels[2].set_text(self.labels[2].originaltext % (self.tw, self.th))
        self.labels[3].set_text(self.labels[3].originaltext % (str(self.btiles)))
        super().blit()

    def resize(self):
        super().resize()

    def send(self, message):
        if message[0] == "-":
            getattr(self, message[1:])()

    def as_left(self):
        try:
            val = int(input("Enter number of tiles to be deleted/added: "))
            self.cuteverydata(val, 0, 0, 0)
        except ValueError:
            print("non valid answer")

    def as_top(self):
        try:
            val = int(input("Enter number of tiles to be deleted/added: "))
            self.cuteverydata(0, val, 0, 0)
        except ValueError:
            print("non valid answer")

    def set_width(self):
        try:
            val = int(input("Enter width: "))
            self.cuteverydata(0, 0, self.gw - val, 0)
        except ValueError:
            print("non valid answer")

    def set_height(self):
        try:
            val = int(input(f"Enter height({self.gh}): "))
            self.cuteverydata(0, 0, val - self.gh, 0)
        except ValueError:
            print("non valid answer")

    def cuteverydata(self, x, y, w, h):
        ans = input("Are you sure?(y/n)>> ")
        if ans.lower() == "n":
            return
        self.data["GE"] = self.cutdata(x, y, w, h, self.data["GE"], [[0, []], [0, []], [0, []]])
        print(self.data["GE"][0])
        self.cuttiles(x, y, w, h)
        for num, effect in enumerate(self.data["FE"]["effects"]):
            self.data["FE"]["effects"][num]["mtrx"] = self.cutdata(x, y, w, h, effect["mtrx"], 0)
        self.recount()

    def cutdata(self, x, y, w, h, array, default_instance):
        arr = array
        if x >= 0:
            for _ in range(x):
                arr.insert(0, [default_instance for _ in range(len(arr[0]))])
        else:
            arr = arr[-x:]

        if w >= 0:
            for _ in range(w):
                arr.append([default_instance for _ in range(len(arr[0]))])
        else:
            arr = arr[:len(arr) + w]

        if y >= 0:
            for i in range(len(arr)):
                for _ in range(y):
                    arr[i].insert(0, default_instance)
        else:
            for i in range(len(arr)):
                arr[i] = arr[i][-y:]

        if h >= 0:
            for i in range(len(arr)):
                for _ in range(h):
                    arr.append(default_instance)
        else:
            for i in range(len(arr)):
                arr[i] = arr[i][:len(arr) + h]
        return arr

    def cuttiles(self, x, y, w, h):
        cutted = self.cutdata(x, y, w, h, self.data["TE"]["tlMatrix"], [{"tp": "default", "data": 0},
                                                                        {"tp": "default", "data": 0},
                                                                        {"tp": "default", "data": 0}])
        for xp, xv in enumerate(cutted):
            for yp, yv in enumerate(xv):
                for layer, item in enumerate(yv):
                    if item["tp"] == "tileBody":
                        dat = toarr(item["data"][0], "point")
                        dat[0] -= x
                        dat[1] -= y
                        if dat[0] < 0 or dat[1] < 0 or dat[0] > len(self.data["GE"]) or dat[1] > len(self.data["GE"][0]):
                            destroy(self.data["TE"], xp, yp, self.items, layer)
                        else:
                            cutted[xp][yp][layer]["data"][0] = makearr(dat, "point")

        self.data["TE"]["tlMatrix"] = cutted

    def recount_image(self):
        try:
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            self.field = pg.image.load(lev)
            self.imagew, self.imageh = self.field.get_size()
            self.imagewp = self.imagew / image1size - self.ofsleft + 1
            self.imagehp = self.imageh / image1size - self.ofstop + 1
        except FileNotFoundError:
            self.field = None
