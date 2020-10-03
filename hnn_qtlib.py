from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QSplitter
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox
from PyQt5.QtGui import QColor, QPainter, QFont, QPen
from PyQt5.QtCore import QCoreApplication, pyqtSignal, QObject, Qt, QSize
from PyQt5.QtCore import QMetaObject

DEFAULT_CSS = """
QRangeSlider * {
    border: 0px;
    padding: 0px;
}
QRangeSlider #Head {
    background-color: rgba(157, 163, 176, 50);
}
QRangeSlider #Span {
    background-color: rgba(22, 31, 50, 150);
}
QRangeSlider #Span:active {
    background-color: rgba(22, 31, 50, 150);
}
QRangeSlider #Tail {
    background-color: rgba(157, 163, 176, 50);
}
QRangeSlider #LineBox {
    background-color: rgba(255, 255, 255, 0);
}
QRangeSlider > QSplitter::handle {
    background-color: rgba(79, 91, 102, 100);
}
QRangeSlider > QSplitter::handle:vertical {
    height: 4px;
}
QRangeSlider > QSplitter::handle:pressed {
    background: #ca5;
}
"""

def scale(val, src, dst):
    try:
      return ((val - src[0]) / float(src[1]-src[0]) * (dst[1]-dst[0]) + dst[0])
    except ZeroDivisionError:
      return 0 

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("QRangeSlider")
        Form.resize(300, 30)
        Form.setStyleSheet(DEFAULT_CSS)
        self._linebox = QWidget(Form)
        self._linebox.setObjectName("LineBox")
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self._splitter = QSplitter(Form)
        self._splitter.setMinimumSize(QSize(0, 0))
        self._splitter.setMaximumSize(QSize(16777215, 16777215))
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.setObjectName("splitter")
        self._head = QGroupBox(self._splitter)
        self._head.setTitle("")
        self._head.setObjectName("Head")
        self._handle = QGroupBox(self._splitter)
        self._handle.setTitle("")
        self._handle.setObjectName("Span")
        self._tail = QGroupBox(self._splitter)
        self._tail.setTitle("")
        self._tail.setObjectName("Tail")
        self.gridLayout.addWidget(self._splitter, 0, 0, 1, 1)
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("QRangeSlider", "QRangeSlider"))


class Element(QGroupBox):
    def __init__(self, parent, main):
        super(Element, self).__init__(parent)
        self.main = main

    def setStyleSheet(self, style):
        self.parent().setStyleSheet(style)

    def textColor(self):
        return getattr(self, '__textColor', QColor(125, 125, 125))

    def setTextColor(self, color):
        if type(color) == tuple and len(color) == 3:
            color = QColor(color[0], color[1], color[2])
        elif type(color) == int:
            color = QColor(color, color, color)
        setattr(self, '__textColor', color)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.main.drawValues():
            self.drawText(event, qp)
        qp.end()


class Head(Element):
    def __init__(self, parent, main):
        super(Head, self).__init__(parent, main)

    def drawText(self, event, qp):
        qp.setPen(self.textColor())
        qp.setFont(QFont('Arial', 10))
        qp.drawText(event.rect(), Qt.AlignLeft, ("%.3f"%self.main.min()))


class Tail(Element):
    def __init__(self, parent, main):
        super(Tail, self).__init__(parent, main)

    def drawText(self, event, qp):
        qp.setPen(self.textColor())
        qp.setFont(QFont('Arial', 10))
        qp.drawText(event.rect(), Qt.AlignRight, ("%.3f"%self.main.max()))


class LineBox(Element):
    def __init__(self, parent, main):
        super(LineBox, self).__init__(parent, main)

    def drawText(self, event, qp):
        qp.setPen(QPen(Qt.red, 2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
        pos = self.main.valueToPos(self.main.line_value)
        if (pos == 0):
          pos += 1
        qp.drawLine(pos, 0, pos, 50)


class Handle(Element):
    def __init__(self, parent, main):
        super(Handle, self).__init__(parent, main)

    def drawText(self, event, qp):
        pass
        # qp.setPen(self.textColor())
        # qp.setFont(QFont('Arial', 10))
        # qp.drawText(event.rect(), Qt.AlignLeft, str(self.main.start()))
        # qp.drawText(event.rect(), Qt.AlignRight, str(self.main.end()))

    def mouseMoveEvent(self, event):
        event.accept()
        mx = event.globalX()
        _mx = getattr(self, '__mx', None)
        if not _mx:
            setattr(self, '__mx', mx)
            dx = 0
        else:
            dx = mx - _mx
        setattr(self, '__mx', mx)
        if dx == 0:
            event.ignore()
            return
        elif dx > 0:
            dx = 1
        elif dx < 0:
            dx = -1
        s = self.main.start() + dx
        e = self.main.end() + dx
        if s >= self.main.min() and e <= self.main.max():
            self.main.setRange(s, e)


class QRangeSlider(QWidget, Ui_Form):
    endValueChanged = pyqtSignal(int)
    maxValueChanged = pyqtSignal(int)
    minValueChanged = pyqtSignal(int)
    startValueChanged = pyqtSignal(int)
    rangeValuesChanged = pyqtSignal(str, float, float)

    _SPLIT_START = 1
    _SPLIT_END = 2

    def __init__(self, label, parent):
        super(QRangeSlider, self).__init__(parent)
        self.label = label
        self.rangeValuesChanged.connect(parent.updateRangeFromSlider)
        self.setupUi(self)
        self.setMouseTracking(False)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)

        self._linebox_layout = QHBoxLayout()
        self._linebox_layout.setSpacing(0)
        self._linebox_layout.setContentsMargins(0, 0, 0, 0)
        self._linebox.setLayout(self._linebox_layout)
        self.linebox = LineBox(self._linebox, main=self)
        self._linebox_layout.addWidget(self.linebox)
        self._head_layout = QHBoxLayout()
        self._head_layout.setSpacing(0)
        self._head_layout.setContentsMargins(0, 0, 0, 0)
        self._head.setLayout(self._head_layout)
        self.head = Head(self._head, main=self)
        self._head_layout.addWidget(self.head)
        self._handle_layout = QHBoxLayout()
        self._handle_layout.setSpacing(0)
        self._handle_layout.setContentsMargins(0, 0, 0, 0)
        self._handle.setLayout(self._handle_layout)
        self.handle = Handle(self._handle, main=self)
        self.handle.setTextColor((150, 255, 150))
        self._handle_layout.addWidget(self.handle)
        self._tail_layout = QHBoxLayout()
        self._tail_layout.setSpacing(0)
        self._tail_layout.setContentsMargins(0, 0, 0, 0)
        self._tail.setLayout(self._tail_layout)
        self.tail = Tail(self._tail, main=self)
        self._tail_layout.addWidget(self.tail)
        self.setDrawValues(True)

    def min(self):
        return getattr(self, '__min', None)

    def max(self):
        return getattr(self, '__max', None)

    def setMin(self, value):
        setattr(self, '__min', value)
        self.minValueChanged.emit(value)

    def setMax(self, value):
        setattr(self, '__max', value)
        self.maxValueChanged.emit(value)

    def start(self):
        return getattr(self, '__start', None)

    def end(self):
        return getattr(self, '__end', None)

    def _setStart(self, value):
        setattr(self, '__start', value)
        self.startValueChanged.emit(value)

    def setStart(self, value):
        v = self.valueToPos(value)
        self._splitter.splitterMoved.disconnect()
        self._splitter.moveSplitter(v, self._SPLIT_START)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)
        self._setStart(value)

    def _setEnd(self, value):
        setattr(self, '__end', value)
        self.endValueChanged.emit(value)

    def setEnd(self, value):
        v = self.valueToPos(value)
        self._splitter.splitterMoved.disconnect()
        self._splitter.moveSplitter(v, self._SPLIT_END)
        self._splitter.splitterMoved.connect(self._handleMoveSplitter)
        self._setEnd(value)

    def drawValues(self):
        return getattr(self, '__drawValues', None)

    def setLine(self, value):
        self.line_value = value

    def setDrawValues(self, draw):
        setattr(self, '__drawValues', draw)

    def getRange(self):
        return (self.start(), self.end())

    def setRange(self, start, end):
        self.setStart(start)
        self.setEnd(end)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            s = self.start()-1
            e = self.end()-1
        elif key == Qt.Key_Right:
            s = self.start()+1
            e = self.end()+1
        else:
            event.ignore()
            return
        event.accept()
        if s >= self.min() and e <= self.max():
            self.setRange(s, e)

    def setBackgroundStyle(self, style):
        self._tail.setStyleSheet(style)
        self._head.setStyleSheet(style)

    def setSpanStyle(self, style):
        self._handle.setStyleSheet(style)

    def valueToPos(self, value):
        return int(scale(value, (self.min(), self.max()), (0, self.width())))

    def _posToValue(self, xpos):
        return scale(xpos, (0, self.width()), (self.min(), self.max()))

    def _handleMoveSplitter(self, xpos, index):
        self._splitter.handleWidth()
        def _lockWidth(widget):
            width = widget.size().width()
            widget.setMinimumWidth(width)
            widget.setMaximumWidth(width)
        def _unlockWidth(widget):
            widget.setMinimumWidth(0)
            widget.setMaximumWidth(16777215)
        if index == self._SPLIT_START:
            v = self._posToValue(xpos)
            _lockWidth(self._tail)
            if v >= self.end():
                return
            self._setStart(v)
            self.rangeValuesChanged.emit(self.label, v, self.end())
        elif index == self._SPLIT_END:
            # account for width of head
            xpos += 4
            v = self._posToValue(xpos)
            _lockWidth(self._head)
            if v <= self.start():
                return
            self._setEnd(v)
            self.rangeValuesChanged.emit(self.label, self.start(), v)
        _unlockWidth(self._tail)
        _unlockWidth(self._head)
        _unlockWidth(self._handle)

# see https://stackoverflow.com/questions/12182133/pyqt4-combine-textchanged-and-editingfinished-for-qlineedit
class MyLineEdit(QLineEdit):
    textModified = pyqtSignal(str) # (label)

    def __init__(self, contents, label, parent=None):
        super(MyLineEdit, self).__init__(contents, parent)
        self.editingFinished.connect(self.__handleEditingFinished)
        self.textChanged.connect(self.__handleTextChanged)
        self._before = contents
        self._label = label

    def __handleTextChanged(self, text):
        if not self.hasFocus():
            self._before = text

    def __handleEditingFinished(self):
        before, after = self._before, self.text()
        if before != after:
            self._before = after
            self.textModified.emit(self._label)