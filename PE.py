import math

from menuclass import *
import random as rnd
from rope import RopeModel

values = {
    "release": {
        -1: "left",
        1: "right",
        "def": "none"
    },
    "renderTime": {
        0: "Pre Effcts",  # ?
        "def": "Post Effcts"
    },
    "variation": {
        0: "random"
    },
    "applyColor": {
        0: "NO",
        "def": "YES"
    },
    "color": {
        0: "NONE"
    },
}


class PE(MenuWithField):
    def __init__(self, process):
        self.menu = "PE"

        self.props: ItemData = process.manager.props
        self.propcolors = process.manager.propcolors

        self.reset_settings()
        self.settingslist = []
        self.matshow = False

        self.depth = 0

        self.normheight = 0

        self.selectedprop = self.props[0]["items"][0]
        self.selectedimage: pg.Surface = self.selectedprop["images"][0]
        self.ropeobject = None
        self.snap = False
        self.notes = []

        self.quads = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.quadsnor = self.quads.copy()  # quad's default position
        self.lastpos = pg.Vector2(0, 0)

        self.prop_settings = {}

        self.helds = [False] * 4
        self.helppoins = pg.Vector2(0, 0)
        self.helppoins2 = pg.Vector2(0, 0)

        self.delmode = False
        self.copymode = False
        self.renderprop = True
        self.modpress = False

        super().__init__(process, "PE")
        self.drawprops = True
        self.selector = widgets.Selector(self, self.props, "s1", "props.txt")
        self.selector.callback = self.selectorset
        self.setprop(self.props[0]["items"][0]["nm"], self.props.categories[0])
        self.resize()
        self.rfa()

    def rotate_select(self):
        val = self.askint("Type prop rotation", False)
        if val is None:
            return
        self.transform_reset()
        self.rotate(val)

    def changematshow(self):
        self.selector.catswap()

    def selectorset(self, buttondata):
        self.setprop(buttondata["nm"], buttondata["category"])

    def renderfield(self):
        super().renderfield()
        self.updateproptransform()

    def getval(self, params, value):
        if params not in values.keys():
            return value
        if value in values[params].keys():
            return values[params][value]
        elif "def" in values[params].keys():
            return values[params]["def"]
        else:
            if params == "color":
                return self.propcolors[value]
            return value

    def settingsupdate(self):
        self.settingslist = []
        for count, item in enumerate(self.prop_settings.items()):
            name, val = item
            rect = pg.rect.Rect(self.settings["s2"]["settingspos"])
            rect = rect.move(0, rect.h * count)
            btn = widgets.Button(self.surface, rect, self.settings["s2"]["settingscolor"], name, onpress=self.changesettings,
                                 tooltip=str(self.getval(name, val)))
            self.settingslist.append(btn)
        self.resize()

    def changesettings(self, button: widgets.Button):
        name = button.text
        try:
            match name:
                case "release":
                    val = (self.prop_settings[name] + 2) % 3 - 1
                case "renderTime":
                    val = (self.prop_settings[name] + 1) % 2
                case "customDepth":
                    val = self.prop_settings[name] % 30 + 1
                case "variation":
                    val = (self.prop_settings[name] + 1) % len(self.selectedprop["images"])
                    self.updateproptransform()
                case "thickness":
                    val = self.prop_settings[name] % 5 + 1
                case "applyColor":
                    val = (self.prop_settings[name] + 1) % 2
                case "color":
                    val = (self.prop_settings[name] + 1) % len(self.propcolors)
                case _:
                    val = self.askint(f"value for {name} property({self.prop_settings[name]})", defaultnumber=self.prop_settings[name])
                    val = int(val)
            self.prop_settings[name] = val
        except (ValueError, TypeError):
            print("non-valid value!")
        self.settingsupdate()

    def change_variation_up(self):
        if self.prop_settings.get("variation") is None:
            return
        val = (self.prop_settings["variation"] + 1) % len(self.selectedprop["images"])
        self.prop_settings["variation"] = val
        self.updateproptransform()

    def change_variation_down(self):
        if self.prop_settings.get("variation") is None:
            return
        val = (self.prop_settings["variation"] - 1)
        if val < 0:
            val = len(self.selectedprop["images"]) - 1
        self.prop_settings["variation"] = val
        self.updateproptransform()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            self.field.resize()
            for i in self.settingslist:
                i.resize()
            self.renderfield()

    def blit(self):
        super().blit()
        self.labels[2].set_text(self.labels[2].originaltext + str(self.prop_settings))
        self.labels[0].set_text(self.labels[0].originaltext + "\n".join(self.notes))
        self.selector.blit()
        mpos = pg.Vector2(self.mousepos)
        for button in self.settingslist:
            button.blitshadow()
        for button in self.settingslist:
            button.blit(sum(pg.display.get_window_size()) // 120)
        if self.onfield or any(self.helds):

            realpos = mpos - self.field.rect.topleft
            s2 = self.size / 2
            pos2 = pg.Vector2(round(math.floor(realpos.x / s2) * s2 - self.selectedimage.get_width() / 2, 4),
                              round(math.floor(realpos.y / s2) * s2 - self.selectedimage.get_height() / 2, 4))
            pos2 += self.field.rect.topleft

            posoffset = self.posoffset * spritesize
            bp = self.getmouse
            self.delmode = self.findparampressed("delete_mode")
            self.copymode = self.findparampressed("copy_mode")
            self.renderprop = not self.delmode and not self.copymode
            if self.copymode:
                widgets.fastmts(self.surface, "Copy prop", mpos.x - 200, mpos.y, white)
            elif self.delmode:
                widgets.fastmts(self.surface, "Delete prop", mpos.x - 200, mpos.y, white)
            if self.lastpos != mpos and self.selectedprop["tp"] == "rope":
                self.lastpos = mpos.copy()
                ropepos = (mpos - pg.Vector2(self.field.rect.topleft)) / self.size * image1size - pg.Vector2(self.xoffset, self.yoffset) * image1size
                pA = pg.Vector2((self.quads[0][0] + self.quads[3][0]) / 2,
                                (self.quads[0][1] + self.quads[3][1]) / 2) + ropepos
                pB = pg.Vector2((self.quads[1][0] + self.quads[2][0]) / 2,
                                (self.quads[1][1] + self.quads[2][1]) / 2) + ropepos
                collDep = ((self.layer - 1) * 10) + self.depth + self.selectedprop["collisionDepth"]
                if collDep < 10:
                    cd = 0
                elif collDep < 20:
                    cd = 1
                else:
                    cd = 2
                fac = (pg.Vector2(self.quads[0]).distance_to(pg.Vector2(self.quads[3]))) / self.normheight
                self.ropeobject = RopeModel(self.data, pA, pB, self.selectedprop, fac, cd,
                                            self.prop_settings["release"])

            # pg.draw.circle(self.fieldmap, red, pg.Vector2(posoffset) / image1size * self.size, 20)

            s = [self.findparampressed("stretch_topleft"),
                 self.findparampressed("stretch_topright"),
                 self.findparampressed("stretch_bottomright"),
                 self.findparampressed("stretch_bottomleft")
                ]

            qd = quadsize(self.quads)
            mosts = qd[2]

            self.if_set(s[0], 0)
            self.if_set(s[1], 1)
            self.if_set(s[2], 2)
            self.if_set(s[3], 3)

            if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                self.mousp = False
                if self.findparampressed("propvariation_change"):
                    self.change_variation_up()
                    self.settingsupdate()
                elif self.delmode:
                    self.modpress = True
                    if len(self.data["PR"]["props"]) > 0:
                        *_, near = self.find_nearest(*posoffset)
                        self.historypop(["PR", "props"], near)
                        self.renderer.props_full_render(self.layer)
                        self.rfa()
                        self.updatehistory()
                elif self.copymode:
                    self.modpress = True
                    if len(self.data["PR"]["props"]) > 0:
                        name, _, near = self.find_nearest(*posoffset)
                        self.setprop(name[1])
                        self.depth = -name[0]
                        quad = []
                        for q in name[3]:
                            quad.append(pg.Vector2(toarr(q, "point")))
                        quads2 = quad.copy()
                        qv = sum(quad, start=pg.Vector2(0, 0)) / 4
                        for i, q in enumerate(quad):
                            vec = pg.Vector2(q) - qv
                            vec = [round(vec.x, 4), round(vec.y, 4)]
                            quads2[i] = vec
                        self.quads = quads2
                        self.prop_settings = name[4]["settings"]
                        self.updateproptransform()
                elif self.selectedprop["tp"] == "long":
                    self.rectdata[0] = posoffset.copy()
                    self.rectdata[1] = mpos.copy()
                    self.transform_reset()
                else:
                    self.place()
            elif bp[0] == 1 and not self.mousp and (self.mousp2 and self.mousp1):
                if self.selectedprop["tp"] == "long" and self.renderprop:
                    self.transform_reset()
                    p1 = self.rectdata[0]
                    p2 = posoffset
                    vec = p2 - p1
                    angle = math.degrees(math.atan2(vec.y, vec.x))
                    distance = p1.distance_to(p2)
                    newquads = self.quadsnor.copy()
                    newquads[1][0] = distance + newquads[0][0]
                    newquads[2][0] = distance + newquads[0][0]
                    q = []
                    point = pg.Vector2(newquads[0])
                    for quad in newquads:
                        newq = pg.Vector2(quad).rotate(angle)
                        if quad[0] < point.x:
                            point.x = quad[0]
                        if quad[1] < point.y:
                            point.y = quad[1]
                        q.append(newq)
                    self.quads = q
                    i, *_, ww, wh = quadtransform(q, self.selectedimage)
                    self.rectdata[2] = pg.Vector2(i.get_size())
                    i = pg.transform.scale(i, [ww / spritesize * self.size, wh / spritesize * self.size])
                    i.set_colorkey(white)
                    self.surface.blit(i, (self.rectdata[1] + mpos) / 2 - pg.Vector2(i.get_size()) / 2)

            elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                self.mousp = True
                if self.selectedprop["tp"] == "long" and self.renderprop and not self.modpress:
                    self.place((self.rectdata[0] + posoffset) / 2)
                    self.transform_reset()
                self.modpress = False

            if bp[2] == 1 and self.mousp2 and (self.mousp and self.mousp1):
                self.mousp2 = False
                if self.findparampressed("propvariation_change"):
                    self.change_variation_down()
                    self.settingsupdate()
                elif self.findparampressed("cursor_propdepth_inverse"):
                    self.depth_down()
                else:
                    self.depth_up()
            elif bp[2] == 0 and not self.mousp2 and (self.mousp and self.mousp1):
                self.mousp2 = True

            if self.renderprop:
                if not any(self.helds):
                    if self.snap:
                        self.surface.blit(self.selectedimage, pos2)
                        p = (pg.Vector2(self.mousepos) - self.field.rect.topleft) / self.size * 2
                        p = pg.Vector2(math.floor(p.x), math.floor(p.y)) * image1size / 2
                        p -= self.offset * image1size
                        widgets.fastmts(self.surface, f"X: {p.x}, Y: {p.y}", mpos.x, mpos.y + 30, white)
                    else:
                        self.surface.blit(self.selectedimage, mpos - pg.Vector2(self.selectedimage.get_size()) / 2)
                        p = (pg.Vector2(self.mousepos) - self.field.rect.topleft) / self.size * image1size
                        p -= self.offset * image1size
                        p = pg.Vector2(round(p.x, 2), round(p.y, 2))
                        widgets.fastmts(self.surface, f"X: {p.x}, Y: {p.y}", mpos.x, mpos.y + 30, white)
                else:
                    q2s = pg.Vector2(mosts[0], mosts[1])
                    self.surface.blit(self.selectedimage, self.helppoins + q2s)
                if self.selectedprop["tp"] == "rope":
                    if not self.findparampressed("pauseropephysics"):
                        self.ropeobject.modelRopeUpdate(not self.findparampressed("disableropecollisions"))
                    color = toarr(self.ropeobject.prop["previewColor"], "color")
                    lastpos = None
                    for segment in self.ropeobject.segments:
                        posofwire = ((pg.Vector2(self.xoffset, self.yoffset) + (segment["pos"]) / image1size) * self.size) + pg.Vector2(self.field.rect.topleft)
                        pg.draw.circle(self.surface, color, posofwire, 5)
                        if lastpos is not None:
                            pg.draw.line(self.surface, white, posofwire, lastpos)
                        lastpos = posofwire
            depthpos = [mpos[0] + 20, mpos[1]]
            if self.findparampressed("propvariation_change"):
                varpos = [mpos[0] + 20, mpos[1] + 60]
                if self.prop_settings.get('variation') == 0:
                    widgets.fastmts(self.surface, "Variation: Random", *varpos, white)
                else:
                    widgets.fastmts(self.surface, f"Variation: {self.prop_settings.get('variation')}", *varpos, white)
            rl = sum(self.selectedprop["repeatL"]) if self.selectedprop.get("repeatL") else self.selectedprop["depth"]
            widgets.fastmts(self.surface, f"Depth: {self.depth} to {rl + self.depth}", *depthpos, white)
            if self.copymode or self.delmode:
                _, _, indx = self.find_nearest(*posoffset)
                if indx != -1:
                    for nearp in self.data["PR"]["props"][indx][3]:
                        near = pg.Vector2(toarr(nearp, "point"))
                        ofc = pg.Vector2(self.xoffset, self.yoffset)
                        pos2 = (near / spritesize + ofc) * self.size + self.field.rect.topleft
                        pg.draw.line(self.surface, red, mpos, pos2, 10)
            self.movemiddle(bp)
        for button in self.settingslist:
            button.blittooltip()
        self.selector.blittooltip()

    def find_nearest(self, x, y):
        mpos = pg.Vector2(x, y)
        near = pg.Vector2(bignum, bignum)
        propnear = []
        nindx = -1
        for indx, prop in enumerate(self.data["PR"]["props"]):
            vec = pg.Vector2(0, 0)
            for point in prop[3]:
                vec += pg.Vector2(toarr(point, "point"))
            vec /= 4
            if vec.distance_to(mpos) < near.distance_to(mpos):
                near = vec
                nindx = indx
                propnear = prop
        return propnear, near, nindx

    def findpropmenu(self):
        nd = {}
        for catnum, item in enumerate(self.props.data):
            cat = self.props.categories[catnum]
            for i in item["items"]:
                nd[i["nm"]] = cat
        name = self.find(nd, "Select a tile")
        if name is None:
            return
        item = self.props[name]
        self.selector.setbyname(name)
        self.setprop(name, item["category"])

    def depth_up(self):
        depth = self.layer * 10
        self.depth = (self.depth + 1 - depth) % 10 + depth
        self.add_warning()

    def depth_down(self):
        maxdepth = self.layer * 10 + 10
        self.depth -= 1
        if self.depth < 0:
            self.depth = maxdepth - 1
        self.add_warning()

    def add_warning(self):
        if self.selectedprop["tp"] not in ["simpleDecal", "variedDecal"]:
            rl = sum(self.selectedprop["repeatL"]) if self.selectedprop.get("repeatL") else self.selectedprop["depth"]
            if self.layer * 10 + self.depth <= 5 and self.layer * 10 + self.depth + rl >= 6:
                self.labels[1].set_text(self.labels[1].originaltext + "this prop will intersect with the play layer!")
                if self.selectedprop["tp"] == "antimatter":
                    self.labels[1].set_text(self.labels[1].originaltext + "Antimatter prop intersecting play layer - remember to use a restore effect on affected play relevant terrain")
            else:
                self.labels[1].set_text(self.labels[1].originaltext)

    def swichlayers(self):
        super().swichlayers()
        self.depth = self.depth % 10 + self.layer * 10
        self.add_warning()

    def swichlayers_back(self):
        super().swichlayers_back()
        self.depth = self.depth % 10 + self.layer * 10
        self.add_warning()

    def if_set(self, pressed, quadindx):
        if pressed and not self.helds[quadindx]:
            self.helds[quadindx] = True
            self.helppoins = pg.Vector2(self.mousepos)
        elif pressed and self.helds[quadindx]:
            self.quads[quadindx] = list(pg.Vector2(self.mousepos) - self.helppoins)
            self.quads[quadindx] = [round(self.quads[quadindx][0], 4), round(self.quads[quadindx][1], 4)]
            self.updateproptransform()
        elif not pressed and self.helds[quadindx]:
            self.helds[quadindx] = False
            self.updateproptransform()

    def browse_next(self):
        self.selector.down()

    def browse_prev(self):
        self.selector.up()

    def cat_next_propupdate(self):
        self.cat_next()

    def cat_prev_propupdate(self):
        self.cat_prev()

    def cat_next(self):
        self.selector.right()

    def cat_prev(self):
        self.selector.left()

    def setprop(self, name, cat=None):
        if hasattr(self, "selector") and self.selector.show == "favs":
            prop = self.selector._favourites[cat, name]
        else:
            prop = self.props[cat, name]
        if hasattr(self, "selector"):
            self.selector.setbyname(name, fromfavs=True)
        if prop is None:
            print("Prop not found in memory! Try relaunch the app")
            return
        self.lastpos = 0
        self.selectedprop = prop.copy()
        self.snap = "snapToGrid" in self.selectedprop["tags"]
        self.recaption()
        self.add_warning()
        self.reset_settings()
        self.applysettings()
        self.transform_reset()
        self.applytags()

    def togglesnap(self):
        self.snap = not self.snap

    def rotate(self, a):
        for indx, quad in enumerate(self.quads):
            rot = rotatepoint(quad, a)
            qx, qy = rot.x, rot.y
            self.quads[indx] = [round(qx, 4), round(qy, 4)]
        self.updateproptransform()

    def flipx(self):
        for indx, quad in enumerate(self.quads):
            self.quads[indx][0] = -quad[0]
        self.updateproptransform()

    def flipy(self):
        for indx, quad in enumerate(self.quads):
            self.quads[indx][1] = -self.quads[indx][1]
        self.updateproptransform()

    def applytags(self):
        tags = self.selectedprop["tags"]
        for tag in tags:
            match tag:
                case "randomRotat":
                    self.rotate(rnd.randint(0, 360))
                case "randomFlipX":
                    self.flipx() if rnd.choice([True, False]) else False
                case "randomFlipY":
                    self.flipy() if rnd.choice([True, False]) else False

    def reset_settings(self):
        self.prop_settings = {"renderorder": 0, "seed": 500, "renderTime": 0}

    def applysettings(self):
        self.prop_settings = {"renderorder": 0, "seed": rnd.randint(0, 1000), "renderTime": 0}
        random = self.selectedprop["random"] if self.selectedprop.get("random") is not None else 1
        notes = self.selectedprop["notes"].copy()
        if self.selectedprop["tp"] in ["standard", "variedStandard"]:
                if self.selectedprop["colorTreatment"] == "bevel":
                    notes.append("The highlights and shadows on this prop are generated by code,\nso it can be rotated to any degree and they will remain correct.\n")
                else:
                    notes.append("Be aware that shadows and highlights will not rotate with the prop,\nso extreme rotations may cause incorrect shading.\n")
                if self.selectedprop["tp"] == "variedStandard":
                    self.prop_settings["variation"] = 0 if random else 1

                if random:
                    notes.append("Will put down a random variation.\nA specific variation can be selected from settings.\n")
                else:
                    notes.append("This prop comes with many variations.\nWhich variation can be selected from settings.\n")
        elif self.selectedprop['tp'] == "rope":
                self.prop_settings["release"] = 0
        elif self.selectedprop["tp"] in ["variedDecal", "variedSoft"]:
            self.prop_settings["variation"] = 0 if random else 1
            self.prop_settings["customDepth"] = self.selectedprop["depth"]
            if self.selectedprop["tp"] == "variedSoft" and self.selectedprop.get("colorize"):
                self.prop_settings["applyColor"] = 1
                notes.append("It's recommended to render this prop after the effects\nif the color is activated, as the effects won't affect the color layers.\n")
        elif self.selectedprop["tp"] in ["simpleDecal", "soft", "softEffect", "antimatter"]:
            self.prop_settings["customDepth"] = self.selectedprop["depth"]

        if self.selectedprop["tp"] == "soft" or self.selectedprop["tp"] == "softEffect" or self.selectedprop["tp"] == "variedSoft":
            if self.selectedprop.get("selfShade") == 1:
                notes.append("The highlights and shadows on this prop are generated by code,\nso it can be rotated to any degree and they will remain correct.\n")
            else:
                notes.append("Be aware that shadows and highlights will not rotate with the prop,\nso extreme rotations may cause incorrect shading.\n")
        if self.selectedprop["nm"].lower() in ["wire", "zero-g wire"]:
            self.prop_settings["thickness"] = 2
            notes.append("The thickness of the wire can be set in settings.\n")
        elif self.selectedprop["nm"].lower() in ["zero-g tube"]:
            self.prop_settings["applyColor"] = 0
            notes.append("The tube can be colored white through the settings.\n")
        for tag in self.selectedprop["tags"]:
            match tag:
                case "customColor":
                    self.prop_settings["color"] = 0
                    notes.append("Custom color available\n")
                case "customColorRainBow":
                    self.prop_settings["color"] = 1
                    notes.append("Custom color available\n")
        newnotes = []
        for note in self.notes:
            if note in newnotes:
                pass
            else:
                newnotes.append(note)
        self.notes = notes
        self.settingsupdate()

    def updateproptransform(self):
        self.loadimage()
        self.selectedimage = quadtransform(self.quads, self.selectedimage)[0]
        self.selectedimage = pg.transform.scale(self.selectedimage, pg.Vector2(self.selectedimage.get_size()) / spritesize * self.size)
        self.selectedimage.set_colorkey(white)
        self.selectedimage.set_alpha(190)

    def loadimage(self):
        var = rnd.randint(0, len(self.selectedprop["images"]) - 1)
        if self.prop_settings.get("variation") not in [None, 0]:
            var = self.prop_settings["variation"] - 1
        self.selectedimage: pg.Surface = self.selectedprop["images"][var]

    def transform_reset(self):
        self.loadimage()

        w, h = self.selectedimage.get_size()
        wd, hd = w / 2, h / 2
        self.quads = [[-wd, -hd], [wd, -hd], [wd, hd], [-wd, hd]]
        self.normheight = pg.Vector2(self.quads[0]).distance_to(pg.Vector2(self.quads[3]))
        self.quadsnor = self.quads.copy()
        self.updateproptransform()

    def addtofavs(self):
        self.selector.addtofavs()

    def showfavs(self):
        self.selector.favourites()

    def place(self, longpos=None):
        if not self.renderprop:
            return 
        quads = self.quads.copy()
        quads2 = quads.copy()
        mousepos = pg.Vector2(self.mousepos)
        posonfield = ((mousepos - pg.Vector2(self.field.rect.topleft)) / self.size - pg.Vector2(self.xoffset, self.yoffset)) * spritesize
        if self.snap:
            realpos = mousepos - self.field.rect.topleft
            posonfield = pg.Vector2(
                round(math.floor(realpos.x / (self.size / 2)) * (spritesize / 2) - self.xoffset * spritesize, 4),
                round(math.floor(realpos.y / (self.size / 2)) * (spritesize / 2) - self.yoffset * spritesize, 4))
        qv = []
        for i, q in enumerate(quads):
            vec = pg.Vector2(q)
            qv.append(vec)
        qv = sum(qv, start=pg.Vector2(0, 0)) / 4
        for i, q in enumerate(quads):
            vec = pg.Vector2(q) - qv * 2 + posonfield
            if longpos:
                vec = pg.Vector2(q) - qv + longpos  # I literally have no idea how this works
            vec = [round(vec.x, 4), round(vec.y, 4)]
            quads2[i] = makearr(vec, "point")
        newpropsettings = self.prop_settings.copy()
        if self.prop_settings.get("variation") is not None:
            if self.prop_settings["variation"] == 0:  # random
                newpropsettings["variation"] = rnd.randint(1, len(self.selectedprop["images"]))
        prop = [-self.depth, self.selectedprop["nm"], makearr(self.selectedprop["cat"], "point"), quads2, {"settings": newpropsettings}]
        if self.selectedprop["tp"] == "rope":
            points = []
            for segment in self.ropeobject.segments:
                point = [segment["pos"].x, segment["pos"].y]
                point = makearr([round(point[0], 4), round(point[1], 4)], "point")
                points.append(point)
            prop[4]["points"] = points
        self.historyappend(["PR", "props"], prop.copy())
        # self.data["PR"]["props"].append(prop.copy())
        self.applytags()
        self.renderer.props_full_render(self.layer)
        self.rfa()
        self.updatehistory()

    def rotate_right(self):
        if self.findparampressed("rotate_speedup"):
            self.rotate(globalsettings["PErotate_speedup"])
        else:
            self.rotate(globalsettings["PErotate_speed"])

    def rotate_left(self):
        if self.findparampressed("rotate_speedup"):
            self.rotate(-globalsettings["PErotate_speedup"])
        else:
            self.rotate(-globalsettings["PErotate_speed"])

    def rotate0(self):
        self.transform_reset()

    def rotate90(self):
        self.transform_reset()
        self.rotate(90)

    def rotate180(self):
        self.transform_reset()
        self.rotate(180)

    def rotate270(self):
        self.transform_reset()
        self.rotate(270)

    def stretch(self, axis, pos):
        for i, q in enumerate(self.quads):
            if q[axis] > 0:
                self.quads[i][axis] += pos
            else:
                self.quads[i][axis] -= pos
        self.updateproptransform()

    def stretchy_up(self):
        self.stretch(1, globalsettings["PEstretch_speed"] * (6 if self.findparampressed("scale_speedup") else 1))

    def stretchy_down(self):
        self.stretch(1, -globalsettings["PEstretch_speed"] * (6 if self.findparampressed("scale_speedup") else 1))

    def stretchx_up(self):
        self.stretch(0, globalsettings["PEstretch_speed"] * (6 if self.findparampressed("scale_speedup") else 1))

    def stretchx_down(self):
        self.stretch(0, -globalsettings["PEstretch_speed"] * (6 if self.findparampressed("scale_speedup") else 1))

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Selected prop: {self.selectedprop['nm']}"
        except TypeError:
            return super().custom_info
