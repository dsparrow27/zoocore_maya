import os
import pprint
from functools import partial

from zoo.libs.plugin import pluginmanager, plugin
from zoo.libs.utils import filesystem
from zoo.libs.maya.qt import mayaui
from qt import QtWidgets
from zoo.libs.utils import classtypes
from zoo.libs.utils import general
from zoo.libs.utils import zlogging
from zoo.libs.command import executor
from maya import cmds

logger = zlogging.getLogger(__name__)


class InvalidJsonFileFormat(Exception):
    """Raised in case of invalid formatted json file(.mmlayout)
    """
    pass


class Translator(plugin.Plugin):
    """This class is the base class for all marking menu action translators.

    The purpose of the translator is to convert the marking menu arguments to suitable arguments
    before the action command is executed.
    :example:
        def translator(self, **kwargs):
            return {"components": kwargs["nodes"]}
    """
    id = ""

    def translate(self, **kwargs):
        """This function is called when the marking menu action is executed.

        :param kwargs: marking menu action arguments to translate, the {"nodes": [om2.MObjectHandle]}
        :type kwargs: dict
        :return: The translated arguments to pass to the executing function
        :rtype: dict

        """
        pass


def findLayout(layoutId):
    """Finds the layout by Id(str) from the layout registry

    :param layoutId: the layout str id, "some.layout.id"
    :type layoutId: str
    :return: If the registry has the id then a :class:`Layout` object will be returned
    :rtype: :class:`Layout` or None
    """
    reg = LayoutRegistry()
    if layoutId in reg.layouts:
        return reg.layouts[layoutId]


class LayoutRegistry(object):
    """This holds all currently available layout classes discovered in the environment
    use :func:`findLayout` to get the layout from this registry.

    To setup the environment you need to set the environment variable :env:'ZOO_MM_LAYOUT_PATH'
    to the directories of the layout, each path should be separated using :class:`os.pathsep`
    """
    LAYOUT_ENV = "ZOO_MM_LAYOUT_PATH"
    MENUS_ENV = "ZOO_MM_MENUS_PATH"
    TRANSLATOR_ENV = "ZOO_MM_TRANSLATOR_PATH"
    __metaclass__ = classtypes.Singleton

    def __init__(self):
        self.layouts = {}
        self.translatorRegistry = pluginmanager.PluginManager(interface=Translator, variableName="id")
        self.customMenuRegistry = pluginmanager.PluginManager(interface=MarkingMenu, variableName="id")
        self.registerLayoutByEnv(LayoutRegistry.LAYOUT_ENV)
        self.customMenuRegistry.registryByEnv(LayoutRegistry.MENUS_ENV)
        self.translatorRegistry.registerPaths(LayoutRegistry.TRANSLATOR_ENV)

    def registerLayoutByEnv(self, env):
        """Recursively Registers all layout files with the extension .mmlayout and loads the json data with a layout
        instance then adds to the layouts cache

        :param env: the environment variable pointing to the parent directory
        :type env: str
        """
        paths = os.environ.get(env, "").split(os.pathsep)
        for p in paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    layoutFile = os.path.join(root, f)
                    try:
                        if f.endswith(".mmlayout"):
                            data = filesystem.loadJson(layoutFile)
                            self.layouts[data["id"]] = Layout(data)
                    # If the Json data is invalid(formatted) it will raise a valueError without a file location
                    # so raise something useful
                    except ValueError:
                        raise InvalidJsonFileFormat("Layout file: {} is invalid possibly due to the "
                                                    "formatting.".format(layoutFile),
                                                    exc_info=True)

    def registerLayoutData(self, data):
        """Adds the layout data structure as a :class:`Layout` using the data["id"] as the
        key.

        :param data: see :class`Layout`
        :type data: dict
        """
        self.layouts[data["id"]] = Layout(data)


class Layout(object):
    """

    .. code-block:: python

        layoutData={"items":{"N": "",
                              "NW": "",
                              "W": "",
                              "SW": "",
                              "S": "",
                              "SE": "",
                              "E": "",
                              "NE": "",
                              "generic": [{"type": "menu",
                                          "name": "Testmenu",
                                          "children": [{"type": "python",
                                                        "command": "",
                                                        "commandUi": ""}
                                                        ]
                                          ]

                              },
                    "id": "some.layout.id"}
        layoutObj = Layout(layoutData)

    """

    #: zoo Command Executor which will be used by the menu item to execute commands
    executor = executor.Executor()

    def __init__(self, data):
        """
        :param data: The layout dict usually loaded from a json .mmlayout file
        :type data: dict
        """
        self.data = data
        self.id = data["id"]
        self.solved = False

    def __repr__(self):
        return "Layout: {}".format(pprint.pformat(self.data))

    def __getitem__(self, item):
        """
        :param item: The name of the layout region eg. "N", "S" etc
        :type item: str
        :return: Will return a dict in cases of marking menu region(n,s,w etc) being a nested after a layout has been \
        solved, a list will be returned for the generic region , str is return when the layout hasnt been solved but \
        references another layout.
        :rtype: list or dict or str
        """
        return self.data.get(item)

    def __iter__(self):
        """Generator that loops the layout items

        :rtype: tuple(str, dict value)
        """
        for name, data in iter(self.data.items()):
            yield name, data

    def items(self):
        """ Returns the item dict for this layout in the form of::

            {"N": "",
            "NW": "",
            "W": "",
            "SW": "",
            "S": "",
            "SE": "",
            "E": "",
            "NE": "",
            "generic": [{"type": "menu",
                      "name": "Testmenu",
                      "children": [{"type": "python",
                                    "command": "",
                                    "commandUi": ""}
                                    ]
                      ]

            }

        :return: The layout items dict
        :rtype: dict
        """
        return self.data["items"].items()

    def merge(self, layout):
        """Merges the layout items into this instance, only differences will be merged.

        :param layout: the layout to merge into the this class
        :type layout: :class:`Layout`
        """
        self.data = general.merge(self.data, layout.data["items"])
        self.solve()

    def validate(self, layout=None):
        """Recursively validates the layout, returning all failed items, if an item references another layout that
        layout will used be validated.

        :param layout: The layout instance to solve
        :type layout: Layout
        :return: the failed items
        :rtype: list
        """
        layout = layout or self
        failed = []
        for item, data in iter(layout["items"].items()):
            if not data:
                continue
            elif isinstance(data, Layout):
                failed.extend(self.validate(data))
            elif item == "generic":
                failed.extend(self._validateGeneric(data))
            elif data.get("type", "") == "python":
                continue
            elif data.get("type", "") == "zooCommand":
                command = self.executor.findCommand(data["command"])
                if not command:
                    failed.append(data)

            else:
                failed.append(data)
        return failed

    def _validateGeneric(self, data):
        """Validates the generic items list to ensure that all commands are valid within the executor

        :param data: the generic items list from the layout
        :type data: list
        :return: the invalid items
        :rtype: list
        """
        failed = []
        for item in iter(data):
            commandType = item["type"]
            # cant validate python commands without executing them?
            if commandType == "python":
                continue
            elif commandType == "menu":
                failed.extend(self._validateGeneric(item["children"]))
            elif commandType == "zooCommand":
                command = self.executor.findCommand(item)
                if not command:
                    failed.append(item)
                continue
            else:
                failed.append(item)

        return failed

    def solve(self):
        """Recursively solves the layout by expanding any @layout.id references which will compose a single dict ready
        for use.

        A layout can contain deeply nested layouts which is referenced by the syntax @layout.id, in the case
        where there is a reference then that layout will be solved first.

        :return: Whether or not the layout was solved
        :rtype: bool
        """
        registry = LayoutRegistry()
        solved = False
        for item, data in self.data["items"].items():
            if not data:
                continue
            elif item == "generic":
                solved = True
                continue
            elif data["type"] == "layout":
                subLayout = registry.layouts.get(data["command"])
                if not subLayout:
                    logger.warning("No layout with the id {}, skipping".format(data))
                    continue
                subLayout.solve()
                self.data[item] = subLayout
                solved = True

        self.solved = solved
        return solved


class MarkingMenu(object):
    """Maya MarkingMenu wrapper object to support zoocommands and python executable code. MM layouts are defined by the
    Layout instance class
    """
    id = ""

    def __init__(self, layout, name, parent, commandExecutor):
        """
        :param layout: the markingMenu layout instance
        :type layout: :class:`Layout`
        :param name: The markingMenu name
        :type name: str
        :param parent: The fullpath to the parent widget
        :type parent: str
        :param commandExecutor: The command executor instance
        :type commandExecutor: :class:`zoo.libs.command.executor.Executor`
        """
        self.layout = layout
        self.name = name
        self.commandExecutor = commandExecutor
        self.parent = parent
        self.popMenu = None  # the menu popup menu, gross thanks maya
        # Arguments that will be passed to the menu item command to be executed
        self.commandArguments = {}
        if cmds.popupMenu(name, ex=True):
            cmds.deleteUI(name)

        self.options = {"allowOptionBoxes": False,
                        "altModifier": False,
                        "button": 1,
                        "ctrlModifier": False,
                        "postMenuCommandOnce": True,
                        "shiftModifier": False}

    def asQObject(self):
        """Returns this markingMenu as a PYQT object

        :return: Return this :class:`MarkingMenu` as a :class:`qt.QMenu` instance
        :rtype: QMenu
        """
        return mayaui.toQtObject(self.name, widgetType=QtWidgets.QMenu)

    def attach(self, **arguments):
        """Generate's the marking menu using the parent marking menu.

        The arguments passed will be passed to ech and every menuItem command, for example if
        the menu item command is a zoocommand then the zoocommand will have the arguments passed to it.

        :param arguments: A Dict of arguments to pass to each menuItem command.
        :type arguments: dict
        :return: if the parent menu doesn't exist then False will be returned, True if successfully attached
        :rtype: bool
        """
        if cmds.popupMenu(self.parent, exists=True):
            self.commandArguments = arguments
            self._show(self.parent, self.parent)
            return True
        return False

    def create(self, **arguments):
        """Create's a new popup markingMenu parented to self.parent instance, use :func: `MarkingMenu:attach` if you
        need to add to existing markingmenu.

        :return: current instance
        :rtype: :class:`MarkingMenu`
        """
        if cmds.popupMenu(self.name, exists=True):
            cmds.deleteUI(self.name)
        self.commandArguments = arguments
        self.popMenu = cmds.popupMenu(self.name, parent=self.parent,
                                      markingMenu=True, postMenuCommand=self._show,
                                      **self.options)
        return self

    def _show(self, menu, parent):
        cmds.setParent(menu, menu=True)
        cmds.menu(menu, edit=True, deleteAllItems=True)

        self.show(self.layout, menu, parent)

    def kill(self):
        if cmds.popupMenu(self.name, ex=True):
            cmds.deleteUI(self.name)

    def addCommand(self, item, parent, radialPosition=None):
        command = self.commandExecutor.findCommand(item["command"])
        if command is None:
            logger.warning("Failed To find Command: {}".format(item["command"]))
            return
        commandAction = command.commandAction(uiType=1, parent=parent)
        commandAction.triggered.connect(partial(self.executeCommand, command))
        if radialPosition:
            cmds.menuItem(commandAction.item, e=True, radialPosition=radialPosition.upper())
        return commandAction

    def addPythonCommand(self, item, parent, radialPosition=None):
        menuItem = cmds.menuItem(label=item["label"], command=partial(self.executePythonCommand,
                                                                      item["command"]),
                                 parent=parent)
        optionBox = item.get("optionBox", False)
        if optionBox:
            cmds.menuItem(parent=parent, optionBox=optionBox, command=item["commandUi"])
        if radialPosition:
            cmds.menuItem(menuItem.item, e=True, radialPosition=radialPosition.upper())

    def _buildGeneric(self, data, menu):
        for item in data:
            if item["type"] == "zooCommand":
                self.addCommand(item, menu)
                continue
            elif item["type"] == "menu":
                subMenu = cmds.menuItem(label=item["label"], subMenu=True)
                self._buildGeneric(item["children"], subMenu)
            elif item["type"] == "python":
                self.addPythonCommand(item, parent=menu)

    def show(self, layout, menu, parent):
        for item, data in layout.items():
            if not data:
                continue
            translator = data.get("translator")
            # menu generic, this is the vertical menu
            if item == "generic":
                self._buildGeneric(data, menu)
                continue
            # nested marking menu
            elif isinstance(data, Layout):
                radMenu = cmds.menuItem(label=data["id"], subMenu=True, radialPosition=item.upper())
                self.show(data, radMenu, parent)
            # radial section of the menus
            elif data["type"] == "zooCommand":
                self.addCommand(data, parent=menu, radialPosition=item.upper())
            elif data["type"] == "python":
                self.addPythonCommand(data, parent=menu, radialPosition=item.upper())

    def executeCommand(self, command, *args):
        """Handles execution of a ZooCommand from the marking menu item

        :param command:
        :type command: :class:`zoo.libs.command.command.ZooCommand`
        """
        # command executor handles errors so just execute it
        self.commandExecutor.execute(command.id, **self.commandArguments)

    def executePythonCommand(self, command, *args):
        pass

    def allowOptionBoxes(self):
        return cmds.popupMenu(self.name, q=True, allowOptionBoxes=True)

    def altModifier(self):
        return cmds.popupMenu(self.name, q=True, altModifier=True)

    def button(self):
        return cmds.popupMenu(self.name, q=True, button=True)

    def ctrlModifier(self):
        return cmds.popupMenu(self.name, q=True, ctrlModifier=True)

    def deleteAllItems(self):
        try:
            cmds.popupMenu(self.name, e=True, deleteAllItems=True)
        except Exception:
            return False
        return True

    def exists(self):
        return cmds.popupMenu(self.name, exists=True)

    def itemArray(self):
        return cmds.popupMenu(self.name, q=True, itemArray=True)

    def markingMenu(self):
        return cmds.popupMenu(self.name, q=True, markingMenu=True)

    def numberOfItems(self):
        return cmds.popupMenu(self.name, q=True, numberOfItems=True)

    def postMenuCommand(self, command):
        cmds.popupMenu(self.name, e=True, postMenuCommand=command)

    def postMenuCommandOnce(self, state):
        cmds.popupMenu(self.name, e=True, postMenuCommandOnce=state)

    def shiftModifier(self):
        return cmds.popupMenu(self.name, q=True, shiftModifier=True)

    def setShiftModifier(self, value):
        return cmds.popupMenu(self.name, e=True, shiftModifier=value)

    def setParent(self, parent):
        return cmds.popupMenu(self.name, e=True, parent=parent.objectName())

    def setCtrlModifier(self, value):
        return cmds.popupMenu(self.name, e=True, ctrlModifier=value)

    def setAltModifier(self, state):
        return cmds.popupMenu(self.name, e=True, altModifier=state)

    def setUseLeftMouseButton(self):
        return cmds.popupMenu(self.name, e=True, button=1)

    def setUseRightMouseButton(self):
        return cmds.popupMenu(self.name, e=True, button=2)

    def setUseMiddleMouseButton(self):
        return cmds.popupMenu(self.name, e=True, button=3)
