import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: emptyState
    color: "transparent"

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16
        width: Math.min(parent.width - 40, 520)

        // Center Art Circle
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 88
            height: 88
            radius: 44
            color: "#161D19"
            border.color: "#2E8B57"
            border.width: 1.5

            Canvas {
                anchors.centerIn: parent
                width: 40
                height: 40
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = "#2E8B57";
                    ctx.lineWidth = 2.2;
                    ctx.lineCap = "round";
                    ctx.lineJoin = "round";
                    // Draw clean studio artboard outline
                    ctx.strokeRect(4, 6, 32, 24);
                    // Draw easel / whiteboard stand legs
                    ctx.beginPath();
                    ctx.moveTo(8, 30);
                    ctx.lineTo(4, 38);
                    ctx.moveTo(32, 30);
                    ctx.lineTo(36, 38);
                    ctx.stroke();
                    // Draw central drawing curve
                    ctx.strokeStyle = "#3FA36D";
                    ctx.lineWidth = 1.8;
                    ctx.beginPath();
                    ctx.moveTo(10, 20);
                    ctx.quadraticCurveTo(18, 12, 24, 22);
                    ctx.lineTo(30, 16);
                    ctx.stroke();
                }
            }
        }

        // Title
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: ((typeof hubBridge !== "undefined" && hubBridge) && hubBridge.searchQuery) ? ("No matching projects for \"" + hubBridge.searchQuery + "\"") : "Welcome to DrawMotion Studio"
            color: "#FFFFFF"
            font.family: "Segoe UI"
            font.pixelSize: 20
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
        }

        // Subtitle
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: ((typeof hubBridge !== "undefined" && hubBridge) && hubBridge.searchQuery) ? "Try searching with a different filename or clear the search query." : "Start by creating your first whiteboard animation or open an existing .wip project file."
            color: "#9CA3AF"
            font.family: "Segoe UI"
            font.pixelSize: 13
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Item { Layout.preferredHeight: 8 }

        // Action Buttons Row
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 14

            // If searching: Show Clear Search button
            Button {
                id: clearBtn
                visible: (typeof hubBridge !== "undefined" && hubBridge) && hubBridge.searchQuery.length > 0
                text: "Clear Search"
                onClicked: {
                    if (typeof hubBridge !== "undefined" && hubBridge) {
                        hubBridge.setSearchQuery("");
                    }
                }

                background: Rectangle {
                    color: clearBtn.hovered ? "#243229" : "#1A2520"
                    border.color: clearBtn.hovered ? "#3FA36D" : "#2E8B57"
                    border.width: 1
                    radius: 8
                }
                contentItem: Text {
                    text: clearBtn.text
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                padding: 10
                leftPadding: 20
                rightPadding: 20
            }

            // Normal Empty Library Buttons
            Button {
                id: createBtn
                visible: !(typeof hubBridge !== "undefined" && hubBridge) || hubBridge.searchQuery.length === 0
                text: "+ Create New Project"
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
                            color: createBtn.pressed ? "#1B5534" : (createBtn.hovered ? "#3FA36D" : "#2E8B57")
                        }
                        GradientStop {
                            position: 1.0
                            color: createBtn.pressed ? "#16452B" : (createBtn.hovered ? "#2E8B57" : "#226B42")
                        }
                    }
                    border.color: createBtn.hovered ? "#56C98B" : "#389B63"
                    border.width: 1
                }
                contentItem: Text {
                    text: createBtn.text
                    color: "#FFFFFF"
                    font.family: "Segoe UI"
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                padding: 10
                leftPadding: 20
                rightPadding: 20
            }

            Button {
                id: openBtn
                visible: !(typeof hubBridge !== "undefined" && hubBridge) || hubBridge.searchQuery.length === 0
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
                leftPadding: 18
                rightPadding: 18
            }
        }
    }
}
