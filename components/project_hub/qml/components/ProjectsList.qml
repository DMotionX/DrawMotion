import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        // Table Header Row
        Rectangle {
            Layout.fillWidth: true
            height: 36
            color: "#131916"
            border.color: "#222C27"
            border.width: 1
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                Text {
                    text: "Project Name"
                    color: "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.fillWidth: true
                }

                Text {
                    text: "Scenes"
                    color: "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.preferredWidth: 80
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    text: "Last Modified"
                    color: "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.preferredWidth: 110
                }

                Text {
                    text: "Size"
                    color: "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.preferredWidth: 80
                }

                Text {
                    text: "Actions"
                    color: "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.preferredWidth: 100
                    horizontalAlignment: Text.AlignRight
                }
            }
        }

        // Project Rows
        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: projectModel

            ScrollBar.vertical: ScrollBar {
                id: listVBar
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: listVBar.hovered ? "#3FA36D" : "#2E8B57"
                }
            }

            delegate: Rectangle {
                id: rowRect
                width: listView.width
                height: 52
                radius: 8
                color: rowMouse.containsMouse ? "#1A2520" : "#141A17"
                border.color: rowMouse.containsMouse ? "#2E8B57" : "#1F2823"
                border.width: 1

                Behavior on color { ColorAnimation { duration: 120 } }
                Behavior on border.color { ColorAnimation { duration: 120 } }

                // Left Emerald Accent Line on hover
                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    radius: 2
                    color: "#2E8B57"
                    visible: rowMouse.containsMouse
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 12

                    // Column 1: Thumbnail Icon + Project Title
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Rectangle {
                            width: 48
                            height: 28
                            radius: 4
                            color: "#101412"
                            clip: true

                            Image {
                                anchors.fill: parent
                                source: model.thumbnail
                                fillMode: Image.PreserveAspectCrop
                                smooth: true
                                asynchronous: true
                            }
                        }

                        Text {
                            text: model.title
                            color: rowMouse.containsMouse ? "#FFFFFF" : "#E5E7EB"
                            font.family: "Segoe UI"
                            font.pixelSize: 13
                            font.bold: true
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }

                    // Column 2: Scenes Count
                    Rectangle {
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: 22
                        radius: 4
                        color: "#1A2520"
                        border.color: "#25342B"
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: model.sceneCount + (model.sceneCount === 1 ? " Scene" : " Scenes")
                            color: "#9CA3AF"
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    // Column 3: Last Modified
                    Text {
                        text: model.lastModified
                        color: "#9CA3AF"
                        font.family: "Segoe UI"
                        font.pixelSize: 12
                        Layout.preferredWidth: 110
                    }

                    // Column 4: File Size
                    Text {
                        text: model.formattedSize
                        color: "#9CA3AF"
                        font.family: "Segoe UI"
                        font.pixelSize: 12
                        Layout.preferredWidth: 80
                    }

                    // Column 5: Actions
                    RowLayout {
                        Layout.preferredWidth: 100
                        spacing: 6
                        Layout.alignment: Qt.AlignRight

                        // Quick Open Button
                        Button {
                            id: openRowBtn
                            z: 10
                            text: "Open"
                            onClicked: hubBridge.openProject(model.path)
                            implicitHeight: 28
                            implicitWidth: 50

                            background: Rectangle {
                                color: openRowBtn.pressed ? "#1B5534" : (openRowBtn.hovered ? "#3FA36D" : "#2E8B57")
                                radius: 5
                            }
                            contentItem: Text {
                                text: openRowBtn.text
                                color: "#FFFFFF"
                                font.family: "Segoe UI"
                                font.pixelSize: 11
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        // 3-Dots Menu Button
                        Button {
                            id: menuRowBtn
                            z: 10
                            text: "⋮"
                            onClicked: listContextMenu.popup()
                            implicitHeight: 28
                            implicitWidth: 28

                            background: Rectangle {
                                color: menuRowBtn.hovered ? "#2A3A31" : "transparent"
                                radius: 14
                            }
                            contentItem: Text {
                                text: menuRowBtn.text
                                color: menuRowBtn.hovered ? "#FFFFFF" : "#9CA3AF"
                                font.pixelSize: 16
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                // Row Main Click Area
                MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    cursorShape: Qt.PointingHandCursor

                    onClicked: (mouse) => {
                        if (mouse.button === Qt.RightButton) {
                            listContextMenu.popup();
                        } else {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.openProject(model.path);
                            }
                        }
                    }
                }

                // Context Menu for List Row
                Menu {
                    id: listContextMenu
                    background: Rectangle {
                        color: "#161D19"
                        border.color: "#2E8B57"
                        border.width: 1
                        radius: 8
                    }

                    Action {
                        text: "Open in Studio"
                        onTriggered: {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.openProject(model.path);
                            }
                        }
                    }

                    Action {
                        text: "Reveal in File Explorer"
                        onTriggered: {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.showInExplorer(model.path);
                            }
                        }
                    }

                    MenuSeparator {
                        contentItem: Rectangle { implicitHeight: 1; color: "#2A3630" }
                    }

                    Action {
                        text: "Remove from Recents"
                        onTriggered: {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.removeRecentProject(model.path);
                            }
                        }
                    }

                    Action {
                        text: "Delete Project File"
                        onTriggered: {
                            if (typeof hubBridge !== "undefined" && hubBridge) {
                                hubBridge.deleteProject(model.path);
                            }
                        }
                    }
                }
            }
        }
    }
}
