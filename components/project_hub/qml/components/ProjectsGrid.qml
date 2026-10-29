import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ScrollView {
        id: scroll
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: ScrollBar {
            id: gridVBar
            policy: ScrollBar.AsNeeded
            contentItem: Rectangle {
                implicitWidth: 6
                radius: 3
                color: gridVBar.hovered ? "#3FA36D" : "#2E8B57"
            }
        }

        Flow {
            id: flowLayout
            width: scroll.availableWidth
            spacing: 16
            topPadding: 2
            bottomPadding: 20

            // 1. Prominent Interactive "+ Create Project" Quick Card
            Rectangle {
                id: newProjectCard
                visible: (typeof hubBridge !== "undefined" && hubBridge) ? hubBridge.searchQuery === "" : true
                width: 260
                height: 220
                radius: 12
                color: newCardMouse.containsMouse ? "#18241E" : "#131916"
                border.color: newCardMouse.containsMouse ? "#2E8B57" : "#222C27"
                border.width: newCardMouse.containsMouse ? 1.5 : 1
                clip: true

                Behavior on color { ColorAnimation { duration: 150 } }
                Behavior on border.color { ColorAnimation { duration: 150 } }

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 10
                    width: parent.width - 36

                    // Plus Icon in Glowing Emerald Circle
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 52
                        height: 52
                        radius: 26
                        color: newCardMouse.containsMouse ? "#243B2E" : "#1A2520"
                        border.color: newCardMouse.containsMouse ? "#3FA36D" : "#2E8B57"
                        border.width: 1.5
                        scale: newCardMouse.containsMouse ? 1.08 : 1.0
                        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }

                        Text {
                            anchors.centerIn: parent
                            text: "+"
                            color: newCardMouse.containsMouse ? "#56C98B" : "#2E8B57"
                            font.pixelSize: 28
                            font.bold: true
                        }
                    }

                    // Title
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Create Project"
                        color: newCardMouse.containsMouse ? "#FFFFFF" : "#E5E7EB"
                        font.family: "Segoe UI"
                        font.pixelSize: 15
                        font.bold: true
                    }

                    // Subtitle
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Start a fresh whiteboard canvas"
                        color: "#9CA3AF"
                        font.family: "Segoe UI"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Item { Layout.preferredHeight: 2 }

                    // Shortcut badge
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        height: 22
                        width: 72
                        radius: 4
                        color: "#1C2621"
                        border.color: "#2E8B57"
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: "Ctrl + N"
                            color: "#3FA36D"
                            font.family: "Segoe UI"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }
                }

                MouseArea {
                    id: newCardMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof hubBridge !== "undefined" && hubBridge) {
                            hubBridge.createNewProject("");
                        }
                    }
                }
            }

            // 2. Project Cards
            Repeater {
                model: projectModel
                ProjectCard {}
            }
        }
    }
}
