import requests
from menus import *
from tkinter.messagebox import askyesnocancel, askyesno
import argparse
from lingotojson import *
from files import settings, hotkeys, path, application_path
import time

widgets.keybol = True
run = True
keys = [pg.K_LCTRL, pg.K_LALT, pg.K_LSHIFT]
movekeys = [pg.K_LEFT, pg.K_UP, pg.K_DOWN, pg.K_RIGHT]
fullscreen = settings["global"]["fullscreen"]
file = ""
file2 = ""
defaultlevel = turntoproject(open(path + "default.txt", "r").read())
undobuffer = [defaultlevel] * globalsettings["historylimit"]
redobuffer = [defaultlevel] * globalsettings["historylimit"]
undobuffer.clear()
redobuffer.clear()
del defaultlevel
surf: Menu | MenuWithField = None
savetimer = time.time()


def openlevel(level, window):
    global run, file, file2, redobuffer, undobuffer, surf
    surf.savef()
    file = level
    if file is not None and os.path.exists(file):
        launchload(file)
        undobuffer = []
        redobuffer = []
        surf.renderer.data = file
        surf.data = file
        surf.renderer.set_surface()
        surf.renderer.render_all(0)
        surf = MN(window, surf.renderer)
        os.system("cls")
    print("Open")


def keypress(window):
    global run, file, file2, redobuffer, undobuffer, surf
    pressed = ""
    ctrl = pg.key.get_pressed()[pg.K_LCTRL]
    # shift = pg.key.get_pressed()[pg.K_LSHIFT]
    for i in hotkeys["global"].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = hotkeys["global"][i]
    for i in hotkeys[surf.menu].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = hotkeys[surf.menu][i]
                surf.send(pressed)
    if len(pressed) > 0 and pressed[0] == "/" and surf.menu != "LD":
        surf.message = pressed[1:]
    match pressed.lower():
        case "undo":
            undohistory()
        case "redo":
            redohistory()
        case "quit":
            asktoexit(file, file2)
        case "reload":
            surf.reload()
        case "save":
            surf.savef()
            file2 = deepcopy(file)
        case "new":
            print("New")
            surf.savef()
            run = False
        case "open":
            openlevel(surf.asksaveasfilename(defaultextension=[".txt", ".wep"]), window)


def undohistory():
    global undobuffer, redobuffer, file, surf
    if len(undobuffer) == 0:
        return
    print("Undo")
    lastsize = [surf.levelwidth, surf.levelheight]
    historyelem = undobuffer[-1]
    '''
    Undo element data:
    [
        [path in level data],
        *[ history step
            [path to level data],
            what changed(after),
            from what changed(before)
        ], and other history steps...
    ]
    '''
    elem = historyelem[1:]
    elem.reverse()
    print("elem: ", historyelem)
    for i in elem:
        print(i)
        if len(i[0]) > 0:  # actions, used to minimize memory cost and improve performance
            match i[0][0]:
                case ".insert": # insert on redo, pop on undo
                    surf.data[*historyelem[0], *i[0][1:]].pop(i[1])
                    continue
                case ".append": # append on redo, pop on undo
                    surf.data[*historyelem[0], *i[0][1:]].pop(-1)
                    continue
                case ".pop": # pop on redo, insert on undo
                    surf.data[*historyelem[0], *i[0][1:]].insert(i[1], i[2])
                    continue
                case ".move": # pop and insert on redo, pop and insert on undo
                    surf.data[*historyelem[0], *i[0][1:]].insert(i[1], surf.data[*historyelem[0], *i[0][1:]].pop(i[2]))
                    continue
        surf.data[*historyelem[0], *i[0]] = i[1][1]
    redobuffer.append(deepcopy(undobuffer.pop()))
    if [surf.levelwidth, surf.levelheight] != lastsize:
        surf.renderer.set_surface([image1size * surf.levelwidth, image1size * surf.levelheight])
    surf.onundo()
    if MenuWithField in type(surf).__bases__:
        surf.renderer.render_all(surf.layer)
        surf.rfa()
        if hasattr(surf, "rebuttons"):
            surf.rebuttons()


def redohistory():
    global undobuffer, redobuffer, file, surf
    if len(redobuffer) == 0:
        return
    print("Redo")
    lastsize = [surf.levelwidth, surf.levelheight]
    historyelem = redobuffer[-1]

    elem = historyelem[1:]
    elem.reverse()
    for i in elem:
        print(i)
        if len(i[0]) > 0:  # actions, used to minimize memory cost and improve performance
            match i[0][0]:
                case ".insert":  # insert on redo, pop on undo
                    surf.data[*historyelem[0], *i[0][1:]].insert(i[1], i[2])
                    continue
                case ".append":  # append on redo, pop on undo
                    surf.data[*historyelem[0], *i[0][1:]].append(i[1])
                    continue
                case ".pop":  # pop on redo, insert on undo
                    surf.data[*historyelem[0], *i[0][1:]].pop(i[1])
                    continue
                case ".move":  # pop and insert on redo, pop and insert on undo
                    surf.data[*historyelem[0], *i[0][1:]].insert(i[2], surf.data[*historyelem[0], *i[0][1:]].pop(i[1]))
                    continue
        surf.data[*historyelem[0], *i[0]] = i[1][0]

    undobuffer.append(deepcopy(redobuffer.pop()))
    if [surf.levelwidth, surf.levelheight] != lastsize:
        surf.renderer.set_surface([image1size * surf.levelwidth, image1size * surf.levelheight])
    surf.onredo()
    if MenuWithField in type(surf).__bases__:
        surf.renderer.render_all(surf.layer)
        surf.rfa()
        if hasattr(surf, "rebuttons"):
            surf.rebuttons()


def asktoexit(file, file2):
    global run, surf
    if file2 != file:
        ex = askyesnocancel("Exit from RWE+", "Do you want to save Changes?")
        if ex:
            surf.savef()
            sys.exit(0)
        elif ex is None:
            return
        else:
            sys.exit(0)
    else:
        sys.exit(0)


def launchload(level):
    global surf, fullscreen, undobuffer, redobuffer, file, file2, run
    if level == -1:
        file = turntoproject(open(path + "default.txt", "r").read())
        file["level"] = ""
        file["path"] = ""
        file["dir"] = ""
    elif level == "":
        return
    elif level[-3:] == "txt":
        file = turntoproject(open(level, "r").read())
        file["level"] = os.path.basename(level)
        file["path"] = level
        file["dir"] = os.path.abspath(level)
    else:
        file = RWELevel(json.load(open(level, "r")))
        file["level"] = os.path.basename(level)
        file["path"] = level
        file["dir"] = os.path.abspath(level)
    undobuffer = []
    redobuffer = []


def doevents(window, dropfile=True):
    global surf, render
    for event in pg.event.get():
        match event.type:
            case pg.DROPFILE:
                if dropfile:
                    openlevel(event.file, window)
                else:
                    if event.file is not None and os.path.exists(event.file):
                        launch(event.file)
            case pg.QUIT:
                asktoexit(file, file2)
            case pg.WINDOWRESIZED:
                surf.resize()
            case pg.KEYDOWN:
                if event.key not in keys:
                    if widgets.keybol:
                        widgets.keybol = False
                        keypress(window)
            case pg.KEYUP:
                if event.key not in keys:
                    if not widgets.keybol:
                        widgets.keybol = True
            case pg.MOUSEBUTTONDOWN:
                if event.button == 4:
                    surf.send("SU")
                elif event.button == 5:
                    surf.send("SD")


def launch(level):
    global surf, fullscreen, undobuffer, redobuffer, file, file2, run, savetimer

    # loading image
    loadi = loadimage(f"{path}load.png")
    window = pg.display.set_mode(loadi.get_size(), flags=pg.NOFRAME)
    window.blit(loadi, [0, 0])
    pg.display.flip()
    pg.display.update()

    launchload(level)
    items = inittolist(window)
    propcolors = getcolors()
    props = getprops(items, window)
    file2 = deepcopy(file)
    width = settings["global"]["width"]
    height = settings["global"]["height"]

    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * fullscreen))
    pg.display.set_icon(loadimage(path + "icon.png"))
    renderer = Renderer(file, items, props, propcolors)
    renderer.render_all(0)
    surf = MN(window, renderer)
    os.system("cls")
    del loadi
    try:
        request = requests.get("https://api.github.com/repos/timofey260/RWE-Plus/releases/latest", timeout=2)
        if request.status_code == 200:
            gittag = request.json()["tag_name"]
            if tag != gittag:
                print("A new version of RWE+ is available!")
                print(f"Current Version: {tag}, latest: {gittag}")
                print("https://github.com/timofey260/RWE-Plus/releases/latest\n"
                      f"Make sure you don't erase your RWE+ projects in {path2levels} and copy them somewhere!!!")
    except requests.exceptions.ConnectionError:
        print("Cannot find new RWE+ versions")
    except requests.exceptions.ReadTimeout:
        print("Cannot find new RWE+ versions")
    run = True
    while run:
        doevents(window)
        if surf.message != "":
            match surf.message:
                case "undo":
                    undohistory()
                case "redo":
                    redohistory()
                case "%":
                    surf = HK(window, renderer, surf.menu)
                case "quit":
                    asktoexit(file, file2)
                case "fc":
                    fullscreen = not fullscreen
                    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * fullscreen))
                    # pg.display.toggle_fullscreen()
                    surf.resize()
                case "save":
                    surf.savef()
                    file2 = deepcopy(file)
                case "saveas":
                    surf.saveasf()
                    file2 = deepcopy(file)
                case "savetxt":
                    surf.savef_txt()
                    file2 = deepcopy(file)
                case _:
                    if surf.message in menulist:
                        surf = getattr(sys.modules[__name__], surf.message)(window, renderer)
                    else:
                        surf.send(surf.message)
            surf.message = ""
        if len(surf.historybuffer) > 0:
            surf.historybuffer.reverse()
            undobuffer.extend(surf.historybuffer)
            surf.historybuffer = []
            redobuffer = []
            undobuffer = undobuffer[-globalsettings["historylimit"]:]

        if not pg.key.get_pressed()[pg.K_LCTRL]:
            for i in surf.uc:
                if pg.key.get_pressed()[i]:
                    keypress(window)
        if settings[surf.menu].get("menucolor") is not None:
            window.fill(pg.color.Color(settings[surf.menu]["menucolor"]))
        else:
            window.fill(pg.color.Color(settings["global"]["color"]))
        surf.blit()
        if 1 < globalsettings["autosavedelay"] < time.time() - savetimer:
            print("Autosaving...")
            surf.savef()
            savetimer = time.time()
        pg.display.flip()
        pg.display.update()


def loadmenu():
    global surf
    run = True
    width = 1280
    height = 720
    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE)
    renderer = Renderer({"path": ""}, None, None, None, False)
    surf = load(window, renderer)
    pg.display.set_icon(loadimage(path + "icon.png"))
    while run:
        doevents(window, False)
        match surf.message:
            case "new":
                launch(-1)
            case "open":
                file = surf.asksaveasfilename(defaultextension=[".txt", ".wep"])
                if file is not None and os.path.exists(file):
                    launch(file)
            case "tutorial":
                file = turntoproject(open(path2tutorial + "tutorial.txt", "r").read())
                file["path"] = "tutorial"
                renderer = Renderer(file, None, None, None, True)
                surf = TT(window, renderer)
            case "load":
                renderer = Renderer({"path": ""}, None, None, None, False)
                surf = load(window, renderer)
        surf.message = ""
        if not pg.key.get_pressed()[pg.K_LCTRL]:
            for i in surf.uc:
                if pg.key.get_pressed()[i]:
                    keypress(window)
        window.fill(pg.color.Color(settings["global"]["color"]))
        surf.blit()
        pg.display.flip()
        pg.display.update()
    pg.quit()
    exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="RWE+ console", description="Maybe a better, than official LE.\n"
                                     "Tool for making levels for rain world",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.version = tag
    parser.add_argument("filename", type=str, nargs="?", help="Level to load")
    parser.add_argument("-n", "--new", help="Opens new file", dest="new", action="store_true")
    parser.add_argument("-v", "--version", help="Shows current version and exits", action="version")
    parser.add_argument("--render", "-r", dest="renderfiles", metavar="file", nargs="*", type=str,
                        help="Renders levels with drizzle.")
    # parser.parse_args()
    args = parser.parse_args()
    try:
        if args.new:
            launch(-1)
        if args.renderfiles is not None:
            s = f"\"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}\""
            subprocess.run([f"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}", "render", *args.renderfiles], shell=True)
            # os.system(s)
            if not islinux:
                os.system("start " + resolvepath(path2renderedlevels))
            exit(0)
        if args.filename is not None:
            launch(args.filename)
        else:
            loadmenu()
    except FileNotFoundError:
        print("File not found!")
        raise
    except Exception as e:
        # extra save level in case of eny crashes
        f = open(application_path + "\\CrashLog.txt", "w")
        f.write(traceback.format_exc())
        f.write("This is why RWE+ crashed^^^\nSorry")
        if globalsettings["saveoncrash"] and not globalsettings["debugmode"]:
            surf.savef(crashsave=True)
            raise
        traceback.print_exc()
        ex = askyesno("Crash!!!",
                      "Oops! RWE+ seems to be crashed, Crash log saved and showed in console\nDo you want to save "
                      "Level?")
        if ex:
            surf.savef()
        raise