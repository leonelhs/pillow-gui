import PIL.Image
import qtawesome as qta
from PIL import ImageFilter, ImageCms
from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QMenuBar, QSplitter, QStatusBar,
                               QVBoxLayout, QWidget, QMainWindow,
                               QMenu, QToolBar, QGraphicsScene, QFileDialog, QComboBox)

import utils
from Actions import Action, ActionRecents
from Storage import Storage
from UI.widgets.InputGrid import InputGrid
from UI.widgets.ImageGraphicsView import ImageGraphicsView
from UI.widgets.LoadingProgressBar import LoadingProgressBar
from UI.widgets.custom_dialog import CustomDialog
from UI.widgets.grid_sliders import GridSliders
from UI.widgets.tool_box_enhancer import ToolBoxEnhancer


def tr(label):
    return QCoreApplication.translate("MainWindow", label, None)


def displayImage(image, scene, graphics):
    scene.clear()
    scene.addPixmap(image.toqpixmap())
    graphics.setScene(scene)
    graphics.setEnabled(True)
    graphics.redraw()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.selection_box = None
        self.action_rotate = None
        self.action_zoom = None
        self.action_save = None
        self.action_open = None
        self.__image_pat = None
        self.__imageInput = None
        self.__imageOutput = None
        self.__outputPanel = None
        self.__inputPanel = None
        self.__sceneInput = None
        self.__sceneOutput = None

        self.toolBar = None
        self.menuFile = None
        self.menuRecents = None
        self.statusbar = None
        self.menubar = None
        self.progressBar = None
        self.toolBox = None
        self.gridKernel = None
        self.gridMerge = None
        self.kernel_size = None

        self.button_superface = None
        self.indicator_super_resolution = None
        self.controls_super_resolution = None
        self.panel_splitter = None
        self.page_zero_background = None
        self.page_super_resolution = None
        self.main_splitter = None
        self.main_layout = None
        self.central_widget = None

        self.action_open = Action(self, "Open", "fa.folder-open")
        self.action_save = Action(self, "Save as", "fa.save")
        self.action_zoom_in = Action(self, "Zoom", "ei.zoom-in")
        self.action_zoom_out = Action(self, "Zoom", "ei.zoom-out")
        self.action_rotate = Action(self, "Rotate", "mdi6.rotate-right-variant")

        self.action_open.setOnClickEvent(self.__dialogOpenFile)
        self.action_save.setOnClickEvent(self.__dialogSaveFile)
        self.action_zoom_in.setOnClickEvent(self.imageZoomIn)
        self.action_zoom_out.setOnClickEvent(self.imageZoomOut)
        self.action_rotate.setOnClickEvent(self.imageFlip)

        self._setupUi(self)
        self.storage = Storage()
        self.__appendFileRecents()

    def _setupUi(self, main_window):
        icon = qta.icon("fa.picture-o")
        main_window.setWindowIcon(icon)
        main_window.setWindowTitle("Pillow GUI")
        self.central_widget = QWidget(main_window)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_splitter = QSplitter(self.central_widget)
        self.main_splitter.setOrientation(Qt.Horizontal)

        self.__createToolBox()
        self.__createImageViewers()
        self.__createProgressbar()

        main_window.setCentralWidget(self.central_widget)

        self.__createMenubar(main_window)
        self.statusbar = QStatusBar(main_window)
        main_window.setStatusBar(self.statusbar)

        self.__createToolbar(main_window)

        self.__retranslateUI()
        QMetaObject.connectSlotsByName(main_window)

    def imageZoomIn(self):
        self.__inputPanel.scale(1.5, 1.5)

    def imageZoomOut(self):
        self.__inputPanel.scale(0.5, 0.5)

    def imageFlip(self):
        image_working = self.imageInput().rotate(90)
        self.displayImageOutput(image_working)

    def __createToolBox(self):

        self.toolBox = ToolBoxEnhancer(self.main_splitter)

        self.toolBox.addPage("filter", u"Pillow filters")

        controls = self.toolBox.createLayout("filter", GridSliders)
        controls.addSlider("Blur", row=0, callback=self.onSliderBlurChanged)
        controls.addSlider("Box blur", row=1, callback=self.onSliderBoxBlurChanged)
        controls.addSlider("Unsharp", row=2, callback=self.onSliderUnsharpMaskChanged)

        dataX3 = [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]
        dataX5 = [[1, 1, 1, 1, 1],
                  [1, 5, 5, 5, 1],
                  [1, 5, 44, 5, 1],
                  [1, 5, 5, 5, 1],
                  [1, 1, 1, 1, 1]]

        def onKernelSizeChanged(index):
            kernel = {0: {"size": 3, "data": dataX3}, 1: {"size": 5, "data": dataX5}}
            self.gridKernel.build(kernel[index]["data"], kernel[index]["size"])

        self.toolBox.addPage("convolution", u"Convolution filter")
        self.kernel_size = self.toolBox.createWidget("convolution", QComboBox)
        self.kernel_size.addItems(["Size 3x3", "Size 5x5"])
        self.kernel_size.currentIndexChanged.connect(onKernelSizeChanged)
        self.gridKernel = self.toolBox.createLayout("convolution", InputGrid)
        self.gridKernel.build(dataX3, size=(3, 3))
        self.toolBox.addButton("convolution", "Convolution", self.onConvolutionFilter)

        self.toolBox.addPage("kernel", u"Kernel filter")
        self.toolBox.addButton("kernel", "Rank", self.onKernelRankFilter)
        self.toolBox.addButton("kernel", "Median", self.onKernelMedianFilter)
        self.toolBox.addButton("kernel", "Min", self.onKernelMinFilter)
        self.toolBox.addButton("kernel", "Max", self.onKernelMaxFilter)
        self.toolBox.addButton("kernel", "Mode", self.onKernelModeFilter)

        self.toolBox.addPage("builtin", u"Builtin filters")
        self.toolBox.addButton("builtin", "Blur", self.onBuiltinBlur)
        self.toolBox.addButton("builtin", "Contour", self.onBuiltinContour)
        self.toolBox.addButton("builtin", "Detail", self.onBuiltinDetail)
        self.toolBox.addButton("builtin", "Edge enhance", self.onBuiltinEdge)
        self.toolBox.addButton("builtin", "Edge enhance more", self.onBuiltinEdgeMore)
        self.toolBox.addButton("builtin", "Emboss", self.onBuiltinEmboss)
        self.toolBox.addButton("builtin", "Find edges", self.onBuiltinFindEdges)
        self.toolBox.addButton("builtin", "Sharpen", self.onBuiltinSharpen)
        self.toolBox.addButton("builtin", "Smoot", self.onSliderSmootChanged)
        self.toolBox.addButton("builtin", "Smoot more", self.onSliderSmootMoreChanged)

        def onChannelRGB(index):
            self.channelRGB(index)

        self.toolBox.addPage("channels", u"Colors channel")
        self.channels_rgb = self.toolBox.createWidget("channels", QComboBox)
        self.channels_rgb.insertItem(-1, "Select color")
        self.channels_rgb.insertItem(0, "Red")
        self.channels_rgb.insertItem(1, "Green")
        self.channels_rgb.insertItem(2, "Blue")
        self.channels_rgb.currentIndexChanged.connect(onChannelRGB)

        def onChannelLab(index):
            self.channelLab(index)

        self.channels_lab = self.toolBox.createWidget("channels", QComboBox)
        self.channels_lab.insertItem(-1, "Select chanel")
        self.channels_lab.insertItem(0, "Light")
        self.channels_lab.insertItem(1, "A")
        self.channels_lab.insertItem(2, "B")
        self.channels_lab.currentIndexChanged.connect(onChannelLab)

        self.toolBox.addButton("channels", "Gray", self.onChannelGray)

        self.gridMerge = self.toolBox.createLayout("channels", InputGrid)
        self.gridMerge.build([["R", "G", "B"]], size=(1, 3))
        self.toolBox.addButton("channels", "Merge", self.onChannelMerge)

        self.main_splitter.addWidget(self.toolBox)
        self.toolBox.setCurrentIndex(0)

    def __createImageViewers(self):
        self.panel_splitter = QSplitter(self.main_splitter)
        self.panel_splitter.setOrientation(Qt.Horizontal)
        self.__inputPanel = ImageGraphicsView(self.panel_splitter)
        self.panel_splitter.addWidget(self.__inputPanel)
        self.__outputPanel = ImageGraphicsView(self.panel_splitter)
        self.panel_splitter.addWidget(self.__outputPanel)
        self.main_splitter.addWidget(self.panel_splitter)
        self.main_layout.addWidget(self.main_splitter)
        self.__sceneInput = QGraphicsScene()
        self.__sceneOutput = QGraphicsScene()
        self.__inputPanel.setEnabled(False)
        self.__outputPanel.setEnabled(False)

    def __createProgressbar(self):
        self.progressBar = LoadingProgressBar()
        self.progressBar.hide()
        self.main_layout.addWidget(self.progressBar)

    def __createMenubar(self, main_window):
        self.menubar = QMenuBar(main_window)
        main_window.setMenuBar(self.menubar)
        self.menuFile = QMenu(self.menubar)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.action_open)
        self.menuFile.addAction(self.action_save)
        self.menuRecents = QMenu(self.menuFile)
        self.menuFile.addMenu(self.menuRecents)

    def __createToolbar(self, main_window):
        self.toolBar = QToolBar(main_window)
        main_window.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.toolBar.addAction(self.action_zoom_in)
        self.toolBar.addAction(self.action_zoom_out)
        self.toolBar.addAction(self.action_rotate)

    def __retranslateUI(self):
        self.menuFile.setTitle(tr("File"))
        self.menuRecents.setTitle(tr("Open Recent Photo"))
        self.action_open.setShortcut(tr("Ctrl+O"))
        self.action_open.setToolTip(tr("Open Image"))

    def __appendFileRecents(self):
        recents = self.storage.fetchRecents()
        for recent in recents:
            action = ActionRecents(self, recent[0])
            action.setCallback(self.__loadPhoto)
            self.menuRecents.addAction(action)

    def __loadPhoto(self, image_path):
        image = self.readImageFile(image_path)
        self.displayImageInput(image)

    def __dialogOpenFile(self):
        image_path = self.launchDialogOpenFile()
        if image_path:
            self.showMessage("Working image at: %s " % image_path)
            self.storage.insertRecent(image_path)
            self.__loadPhoto(image_path)

    def __dialogSaveFile(self):
        image_path = self.launchDialogSaveFile()
        if image_path:
            self.imageOutput().save(image_path, "PNG")

    def launchDialogOpenFile(self):
        return QFileDialog.getOpenFileName(self, 'Open Image')[0]

    def launchDialogSaveFile(self):
        return QFileDialog.getSaveFileName(self, 'Save Image')[0]

    def readImageFile(self, image_path):
        self.setImagePath(image_path)
        return utils.imageOpen(image_path)

    def displayImageInput(self, image):
        self.__imageInput = image
        displayImage(image, self.__sceneInput, self.__inputPanel)

    def displayImageOutput(self, image):
        self.__imageOutput = image
        displayImage(image, self.__sceneOutput, self.__outputPanel)

    def imageOutput(self):
        return self.__imageOutput

    def imageInput(self):
        if self.__imageInput:
            return self.__imageInput
        else:
            CustomDialog("Alert", "Please load an image.").exec()
            return None

    def imagePath(self):
        return self.__image_pat

    def setImagePath(self, image_path):
        self.__image_pat = image_path

    def inputPanel(self):
        return self.__inputPanel

    def outputPanel(self):
        return self.__outputPanel

    def sceneInput(self):
        return self.__sceneInput

    def sceneOutput(self):
        return self.__sceneOutput

    def showMessage(self, message):
        self.statusbar.showMessage(message)

    def onSliderBlurChanged(self, radius):
        image_working = self.imageInput().filter(ImageFilter.GaussianBlur(radius=radius))
        self.displayImageOutput(image_working)
        self.showMessage("Filter Blur radius: %d " % radius)

    def onSliderBoxBlurChanged(self, radius):
        image_working = self.imageInput().filter(ImageFilter.BoxBlur(radius=radius))
        self.displayImageOutput(image_working)
        self.showMessage("Filter Box Blur radius: %d " % radius)

    def onSliderUnsharpMaskChanged(self, radius):
        image_working = self.imageInput().filter(ImageFilter.UnsharpMask(radius=radius, percent=150, threshold=3))
        self.displayImageOutput(image_working)
        self.showMessage("Filter Unsharp Mask radius: %d " % radius)

    def onKernelRankFilter(self, size=3, rank=0):
        image_working = self.imageInput().filter(ImageFilter.RankFilter(size, rank))
        self.displayImageOutput(image_working)

    def onKernelMedianFilter(self, size=9):
        # Fixme, setting default parameter gets an error
        image_working = self.imageInput().filter(ImageFilter.MedianFilter(size=size))
        self.displayImageOutput(image_working)
        self.showMessage("Filter Median size : %d " % size)

    def onKernelMinFilter(self, size=3):
        image_working = self.imageInput().filter(ImageFilter.MinFilter)
        self.displayImageOutput(image_working)
        self.showMessage("Filter Min size : %d " % size)

    def onKernelMaxFilter(self, size=3):
        image_working = self.imageInput().filter(ImageFilter.MaxFilter)
        self.displayImageOutput(image_working)
        self.showMessage("Filter Max size : %d " % size)

    def onKernelModeFilter(self, size=3):
        image_working = self.imageInput().filter(ImageFilter.ModeFilter)
        self.displayImageOutput(image_working)
        self.showMessage("Filter Model size : %d " % size)

    def onConvolutionFilter(self):
        scale = 1
        offset = 0
        size = self.gridKernel.getSize()
        kernel = self.gridKernel.getIntValues()
        image_working = self.imageInput().filter(ImageFilter.Kernel(size, kernel, scale, offset))
        self.displayImageOutput(image_working)
        self.showMessage("Convolution size : %d " % size[0])

    def onBuiltinBlur(self):
        image_working = self.imageInput().filter(ImageFilter.BLUR())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Blur")

    def onBuiltinContour(self):
        image_working = self.imageInput().filter(ImageFilter.CONTOUR())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Contur")

    def onBuiltinDetail(self):
        image_working = self.imageInput().filter(ImageFilter.DETAIL())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Detail")

    def onBuiltinEdge(self):
        image_working = self.imageInput().filter(ImageFilter.EDGE_ENHANCE())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Edge")

    def onBuiltinEdgeMore(self):
        image_working = self.imageInput().filter(ImageFilter.EDGE_ENHANCE_MORE())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Edge More")

    def onBuiltinEmboss(self):
        image_working = self.imageInput().filter(ImageFilter.EMBOSS())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Emboss")

    def onBuiltinFindEdges(self):
        image_working = self.imageInput().filter(ImageFilter.FIND_EDGES())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Find Edges")

    def onBuiltinSharpen(self):
        image_working = self.imageInput().filter(ImageFilter.SHARPEN())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Sharpen")

    def onSliderSmootChanged(self):
        image_working = self.imageInput().filter(ImageFilter.SMOOTH())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Smoot")

    def onSliderSmootMoreChanged(self):
        image_working = self.imageInput().filter(ImageFilter.SMOOTH_MORE())
        self.displayImageOutput(image_working)
        self.showMessage("Filter Builtin Smoot More")

    def channelRGB(self, color):
        if color >= 0:
            channel = self.imageInput().split()
            self.displayImageOutput(channel[color])
            self.showMessage("Filter channel RGB")

    def onChannelGray(self):
        gray = self.imageInput().convert('L')
        self.displayImageOutput(gray)
        self.showMessage("Filter channel gray")

    def onChannelMerge(self):
        order = self.gridMerge.getValues()
        red, green, blue = self.imageInput().split()
        colors = {"R": red, "G": green, "B": blue}

        def upper(index):
            return order[index].upper()

        merge = (colors[upper(0)], colors[upper(1)], colors[upper(2)])
        image = PIL.Image.merge("RGB", merge)
        self.displayImageOutput(image)
        self.showMessage("Merge channels order: {0}, {1}, {2}".format(order[0], order[1], order[2]))

    def channelLab(self, channel):
        image_working = self.imageInput().convert("RGB")

        # Convert to Lab colourspace
        srgb_p = ImageCms.createProfile("sRGB")
        lab_p = ImageCms.createProfile("LAB")

        rgb2lab = ImageCms.buildTransformFromOpenProfiles(srgb_p, lab_p, "RGB", "LAB")
        channels = ImageCms.applyTransform(image_working, rgb2lab).split()
        self.displayImageOutput(channels[channel])
        self.showMessage("Filter channel Lab")
