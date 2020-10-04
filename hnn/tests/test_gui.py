from PyQt5 import QtWidgets, QtCore

from hnn import HNNGUI


def test_HNNGUI(qtbot):
    main = HNNGUI()
    qtbot.addWidget(main)


def test_exit_button(qtbot, monkeypatch):
    exit_calls = []
    monkeypatch.setattr(QtWidgets.QApplication, "exit",
                        lambda: exit_calls.append(1))
    main = HNNGUI()
    qtbot.addWidget(main)
    qtbot.mouseClick(main.qbtn, QtCore.Qt.LeftButton)
    assert exit_calls == [1]
