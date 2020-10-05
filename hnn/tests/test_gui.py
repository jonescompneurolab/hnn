from PyQt5 import QtWidgets, QtCore
import pytest

from hnn import HNNGUI

@pytest.mark.skip
def test_HNNGUI(qtbot):
    main = HNNGUI()
    qtbot.addWidget(main)

@pytest.mark.skip
def test_exit_button(qtbot, monkeypatch):
    exit_calls = []
    monkeypatch.setattr(QtWidgets.QApplication, "exit",
                        lambda: exit_calls.append(1))
    main = HNNGUI()
    qtbot.addWidget(main)
    qtbot.mouseClick(main.qbtn, QtCore.Qt.LeftButton)
    assert exit_calls == [1]
