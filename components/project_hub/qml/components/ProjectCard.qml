import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: card
    width: 260
    height: 220
    color: cardMouseArea.containsMouse ? "#1C2621" : "#161D19"
    border.color: cardMouseArea.containsMouse ? "#2E8B57" : "#222C27"
    border.width: cardMouseArea.containsMouse ? 1.5 : 1
    radius: 12
    clip: true

    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    // Top Subtle Hover Sheen Glow Line
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 2.5
        visible: cardMouseArea.containsMouse
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: "#3FA36D" }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 1. Thumbnail Canvas Viewport
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 138
            color: "#101412"
            clip: true

            Image {
                id: thumbImg
                anchors.fill: parent
                source: model.thumbnail
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                smooth: true
                scale: cardMouseArea.containsMouse ? 1.04 : 1.0
                Behavior on scale { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
            }

            // Scene Count Badge (Top-Left, Zero Emojis)
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: 10
                height: 22
                width: sceneText.implicitWidth + 16
                radius: 5
                color: "#D90D110F"
                border.color: "#2A3630"
                border.width: 1

                Text {
                    id: sceneText
                    anchors.centerIn: parent
                    text: model.sceneCount + (model.sceneCount === 1 ? " Scene" : " Scenes")
                    color: "#E5E7EB"
                    font.family: "Segoe UI"
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            // WIP Badge (Top-Right)
            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                height: 20
                width: 38
                radius: 4
                color: "#E60F1A14"
                border.color: "#2E8B57"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "WIP"
                    color: "#3FA36D"
                    font.family: "Segoe UI"
                    font.pixelSize: 10
                    font.bold: true
                }
            }

            // Play / Open Center Overlay on Hover
            Rectangle {
                anchors.centerIn: parent
                width: 46
                height: 46
                radius: 23
                color: "#E62E8B57"
                border.color: "#56C98B"
                border.width: 1.5
                visible: cardMouseArea.containsMouse
                opacity: cardMouseArea.containsMouse ? 1.0 : 0.0
                scale: cardMouseArea.containsMouse ? 1.0 : 0.8

                Behavior on opacity { NumberAnimation { duration: 180 } }
                Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }

                Text {
                    anchors.centerIn: parent
                    text: "▶"
                    color: "#FFFFFF"
                    font.pixelSize: 17
                    leftPadding: 3
                }
            }
        }

        // 2. Card Metadata Footer
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 10
                spacing: 8

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        text: model.title
                        color: cardMouseArea.containsMouse ? "#FFFFFF" : "#F3F4F6"
                        font.family: "Segoe UI"
                        font.pixelSize: 14
                        font.bold: true
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }

                    RowLayout {
                        spacing: 6
                        Text {
                            text: model.lastModified
                            color: "#9CA3AF"
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                        }

                        Text {
                            text: "•"
                            color: "#4B5563"
                            font.pixelSize: 11
                        }

                        Text {
                            text: model.formattedSize
                            color: "#9CA3AF"
                            font.family: "Segoe UI"
                            font.pixelSize: 11
                        }
                    }
                }

                // 3-Dots Action Menu Button (z: 10 to ensure priority over card area)
                Button {
                    id: menuBtn
                    z: 10
                    text: "⋮"
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 30
                    background: Rectangle {
                        color: menuBtn.hovered ? "#2A3A31" : "transparent"
                        radius: 15
                        Behavior on color { ColorAnimation { duration: 120 } }
                    }
                    contentItem: Text {
                        text: menuBtn.text
                        color: menuBtn.hovered ? "#FFFFFF" : "#9CA3AF"
                        font.pixelSize: 17
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: contextMenu.popup()
                }
            }
        }
    }

    // Card Main Click & Hover Area
    MouseArea {
        id: cardMouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor

        onClicked: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                contextMenu.popup();
            } else {
                if (typeof hubBridge !== "undefined" && hubBridge) {
                    hubBridge.openProject(model.path);
                }
            }
        }
    }

    // Modern Dark Glass Context Menu
    Menu {
        id: contextMenu
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
