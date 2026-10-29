import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: header
    height: 72
    color: "#131916"
    border.color: "#222C27"
    border.width: 1
    radius: 12

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 16

        // Left Branding: Official Logo + Title + Status Dot + Version Tag
        RowLayout {
            spacing: 14

            Rectangle {
                width: 42
                height: 42
                radius: 10
                color: "#1A241F"
                border.color: "#2E8B57"
                border.width: 1.5

                Image {
                    id: logoImg
                    anchors.centerIn: parent
                    width: 32
                    height: 32
                    source: (typeof appLogoUrl !== "undefined" && appLogoUrl.length > 0) ? appLogoUrl : ""
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    visible: status === Image.Ready
                }

                Text {
                    anchors.centerIn: parent
                    text: "DM"
                    color: "#2E8B57"
                    font.family: "Segoe UI"
                    font.pixelSize: 16
                    font.bold: true
                    visible: !logoImg.visible
                }
            }

            ColumnLayout {
                spacing: 3

                Text {
                    text: "DrawMotion Studio"
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 16
                    font.bold: true
                }

                RowLayout {
                    spacing: 6

                    Rectangle {
                        width: 7
                        height: 7
                        radius: 3.5
                        color: "#10B981"
                    }

                    Text {
                        text: "v" + ((typeof updateBridge !== "undefined" && updateBridge) ? updateBridge.currentVersion : "1.0.0") + " • Projects Hub"
                        color: "#9CA3AF"
                        font.family: "Segoe UI"
                        font.pixelSize: 11
                    }
                }
            }
        }

        Item { Layout.fillWidth: true }

        // Right Actions: Open Project..., + New Project, Open Studio ➔
        RowLayout {
            spacing: 10

            // Open Project button
            Button {
                id: openBtn
                text: "Open Project..."
                onClicked: {
                    if (typeof hubBridge !== "undefined" && hubBridge) {
                        hubBridge.browseProject();
                    }
                }
                
                background: Rectangle {
                    color: openBtn.hovered ? "#22312A" : "#1A241F"
                    border.color: openBtn.hovered ? "#3FA36D" : "#2A3A31"
                    border.width: 1
                    radius: 8
                    Behavior on color { ColorAnimation { duration: 120 } }
                    Behavior on border.color { ColorAnimation { duration: 120 } }
                }
                contentItem: Text {
                    text: openBtn.text
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                padding: 10
                leftPadding: 16
                rightPadding: 16
            }

            // New Project button (Vibrant Emerald Primary Action)
            Button {
                id: newBtn
                text: "+ New Project"
                onClicked: {
                    if (typeof hubBridge !== "undefined" && hubBridge) {
                        hubBridge.createNewProject("");
                    }
                }

                background: Rectangle {
                    radius: 8
                    gradient: Gradient {
                        GradientStop {
                            position: 0.0
                            color: newBtn.pressed ? "#1B5534" : (newBtn.hovered ? "#3FA36D" : "#2E8B57")
                        }
                        GradientStop {
                            position: 1.0
                            color: newBtn.pressed ? "#16452B" : (newBtn.hovered ? "#2E8B57" : "#226B42")
                        }
                    }
                    border.color: newBtn.hovered ? "#56C98B" : "#389B63"
                    border.width: 1
                }
                contentItem: Text {
                    text: newBtn.text
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                padding: 10
                leftPadding: 18
                rightPadding: 18
            }

            // Open Studio button
            Button {
                id: studioBtn
                text: "Open Studio ➔"
                onClicked: {
                    if (typeof hubBridge !== "undefined" && hubBridge) {
                        hubBridge.closeHub();
                    }
                }

                background: Rectangle {
                    color: studioBtn.hovered ? "#23302A" : "transparent"
                    border.color: studioBtn.hovered ? "#3FA36D" : "#2A3A31"
                    border.width: 1
                    radius: 8
                    Behavior on color { ColorAnimation { duration: 120 } }
                }
                contentItem: Text {
                    text: studioBtn.text
                    color: studioBtn.hovered ? "#FFFFFF" : "#9CA3AF"
                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                padding: 10
                leftPadding: 14
                rightPadding: 14
            }
        }
    }
}
